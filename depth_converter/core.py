"""Main depth-video processing pipeline.

This module is UI-agnostic — it knows nothing about Gradio, FastAPI, or any
specific interface.  Callers provide a progress callback that satisfies the
``ProgressCallback`` protocol.
"""

from __future__ import annotations

import gc
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional, Protocol

import cv2
import numpy as np
import torch

from .ffmpeg import (
    ffmpeg_available,
    extract_audio,
    has_audio_stream,
    merge_audio_video,
    write_video_ffmpeg,
)
from .models import (
    MODEL_DEFS,
    RESOLUTION_PRESETS,
    detect_device,
    ensure_checkpoint,
    load_model,
)
from .smoothing import TemporalSmoother, depth_to_grayscale


class ProgressCallback(Protocol):
    """Progress reporting protocol.

    Gradio's ``gr.Progress`` satisfies this natively (its ``__call__``
    accepts ``(fraction: float, desc: str)``).  FastAPI / CLI callers
    can pass a plain function with the same signature.
    """

    def __call__(self, fraction: float, description: str) -> None: ...


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def process_video(
    input_video_path: str,
    model_size_label: str,
    resolution_choice: str,
    invert_bw: bool,
    smoothing_strength: float,    # 0–100
    preserve_audio: bool,
    progress: ProgressCallback | None = None,
) -> str:
    """Run the full depth-conversion pipeline.  Returns path to output MP4.

    Parameters
    ----------
    input_video_path : str
        Path to the source video (.mp4 / .mov).
    model_size_label : str
        One of the keys in ``MODEL_DEFS``.
    resolution_choice : str
        One of the keys in ``RESOLUTION_PRESETS``.
    invert_bw : bool
        If True, swap near ↔ far in the output depth map.
    smoothing_strength : float
        0 = no temporal smoothing, 100 = maximum.
    preserve_audio : bool
        Whether to mux the original audio into the output file.
    progress : callable or None
        ``progress(fraction: float, desc: str)`` — called at key milestones.

    Returns
    -------
    str
        Path to the generated depth-map MP4 file.

    Raises
    ------
    RuntimeError
        If ffmpeg is missing, the video can't be opened, or other user errors.
    """

    def _report(frac: float, desc: str) -> None:
        if progress is not None:
            progress(frac, desc)

    # ------------------------------------------------------------------
    # 0. Validate inputs
    # ------------------------------------------------------------------
    if not input_video_path:
        raise RuntimeError("Please upload a video file first.")

    if not ffmpeg_available():
        raise RuntimeError(
            "ffmpeg is required but was not found.\n\n"
            "macOS:  brew install ffmpeg\n"
            "Windows: winget install ffmpeg"
        )

    # ------------------------------------------------------------------
    # 1. Device & model
    # ------------------------------------------------------------------
    device_str, device_desc = detect_device()

    model = load_model(model_size_label, device_str, progress)

    # ------------------------------------------------------------------
    # 2. Open video
    # ------------------------------------------------------------------
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {input_video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if total_frames < 1:
        cap.release()
        raise RuntimeError("Video contains no frames.")

    target_res = RESOLUTION_PRESETS[resolution_choice]
    if target_res is None:
        out_w, out_h = orig_w, orig_h
    else:
        out_w, out_h = target_res

    # ------------------------------------------------------------------
    # 3. Extract original audio (if requested)
    # ------------------------------------------------------------------
    tmp_dir = tempfile.mkdtemp(prefix="depth_video_")
    audio_path = os.path.join(tmp_dir, "audio.m4a") if preserve_audio else None
    has_audio = False
    if preserve_audio:
        _report(0.05, "Extracting original audio…")
        has_audio = has_audio_stream(input_video_path)
        if has_audio:
            ok = extract_audio(input_video_path, str(audio_path))
            if not ok:
                has_audio = False

    # ------------------------------------------------------------------
    # 4. Read all frames into memory
    # ------------------------------------------------------------------
    _report(0.08, "Reading video frames…")
    raw_frames: list = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if out_w != orig_w or out_h != orig_h:
            frame = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
        raw_frames.append(frame)
    cap.release()
    n_frames = len(raw_frames)
    _report(0.10, f"Read {n_frames} frames  |  Starting depth inference…")

    # ------------------------------------------------------------------
    # 5. Depth inference — uses the official infer_image method
    # ------------------------------------------------------------------
    depth_maps: list = []
    inference_start = time.time()
    for idx, frame_bgr in enumerate(raw_frames):
        frac = 0.10 + 0.70 * (idx / max(n_frames, 1))
        elapsed = time.time() - inference_start
        if idx > 0:
            eta = (elapsed / idx) * (n_frames - idx)
            eta_str = f"{eta:.0f}s remaining"
        else:
            eta_str = "estimating…"
        _report(frac, f"Depth inference  {idx + 1}/{n_frames}  |  {eta_str}")

        depth = model.infer_image(frame_bgr)   # returns float32 ndarray (H, W)
        depth_maps.append(depth)

    _report(0.80, "Depth inference complete  |  Post-processing…")

    if device_str == "cuda":
        torch.cuda.empty_cache()

    # ------------------------------------------------------------------
    # 6. Temporal smoothing + grayscale conversion
    # ------------------------------------------------------------------
    alpha = 1.0 - (smoothing_strength / 100.0) * 0.95
    smoother = TemporalSmoother(alpha)
    output_frames: list = []
    for idx, depth in enumerate(depth_maps):
        frac = 0.80 + 0.10 * (idx / max(n_frames, 1))
        _report(frac, f"Applying smoothing  {idx + 1}/{n_frames}")
        smoothed = smoother.smooth(depth)
        gray = depth_to_grayscale(smoothed, invert=invert_bw)
        # Grayscale → BGR for ffmpeg encoding
        bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        output_frames.append(bgr)

    del raw_frames, depth_maps
    gc.collect()

    # ------------------------------------------------------------------
    # 7. Encode output video (H.264 MP4 via ffmpeg pipe)
    # ------------------------------------------------------------------
    _report(0.90, "Encoding output video (H.264 MP4)…")
    video_no_audio = os.path.join(tmp_dir, "depth_video.mp4")
    stacked = np.stack(output_frames, axis=0)
    write_video_ffmpeg(stacked, fps, video_no_audio)
    del stacked, output_frames
    gc.collect()

    # ------------------------------------------------------------------
    # 8. Mux audio
    # ------------------------------------------------------------------
    if has_audio and audio_path and os.path.exists(str(audio_path)):
        _report(0.95, "Merging original audio…")
        final_path = os.path.join(tmp_dir, "depth_video_with_audio.mp4")
        merge_audio_video(video_no_audio, str(audio_path), final_path)
        result_path = final_path
    else:
        result_path = video_no_audio

    # ------------------------------------------------------------------
    # 9. Copy result to a stable location & clean up
    # ------------------------------------------------------------------
    output_dir = tempfile.mkdtemp(prefix="dv_output_")
    output_file = os.path.join(output_dir, "depth_output.mp4")
    shutil.copy2(result_path, output_file)

    try:
        shutil.rmtree(tmp_dir)
    except OSError:
        pass

    _report(1.0, "Done!")
    return output_file
