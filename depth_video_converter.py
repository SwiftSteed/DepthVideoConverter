#!/usr/bin/env python3
"""
Depth Video Converter — Convert any video to a depth-map video using Depth Anything V2.

Features:
  - Gradio Web UI with MP4 / MOV upload
  - Depth Anything V2 (Small / Base / Large) — local .pth checkpoints
  - Auto-detect NVIDIA CUDA, Apple Silicon MPS, or fallback to CPU
  - Model size selection, output resolution, black/white inversion
  - Temporal smoothing (exponential moving average) to reduce flicker
  - Optional original audio preservation (requires ffmpeg)
  - Export as H.264 MP4 (via ffmpeg pipe)

Author: Claude Code
License: MIT
"""

from __future__ import annotations

import gc
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.request import urlretrieve

import cv2
import gradio as gr
import numpy as np
import torch

# Import the vendored Depth Anything V2 model architecture
from depth_anything_v2 import DepthAnythingV2

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_DIR / "models"

MODEL_DEFS: Dict[str, dict] = {
    "Small (fastest, ~95 MB)": {
        "encoder": "vits",
        "features": 64,
        "out_channels": [48, 96, 192, 384],
        "path": MODELS_DIR / "depth_anything_v2_vits.pth",
        "url": "https://huggingface.co/depth-anything/Depth-Anything-V2-Small/resolve/main/depth_anything_v2_vits.pth",
    },
    "Base (balanced, ~372 MB)": {
        "encoder": "vitb",
        "features": 128,
        "out_channels": [96, 192, 384, 768],
        "path": MODELS_DIR / "depth_anything_v2_vitb.pth",
        "url": "https://huggingface.co/depth-anything/Depth-Anything-V2-Base/resolve/main/depth_anything_v2_vitb.pth",
    },
    "Large (best quality, ~1.2 GB)": {
        "encoder": "vitl",
        "features": 256,
        "out_channels": [256, 512, 1024, 1024],
        "path": MODELS_DIR / "depth_anything_v2_vitl.pth",
        "url": "https://huggingface.co/depth-anything/Depth-Anything-V2-Large/resolve/main/depth_anything_v2_vitl.pth",
    },
}

RESOLUTION_PRESETS: Dict[str, Optional[Tuple[int, int]]] = {
    "Original": None,
    "480p (854×480)": (854, 480),
    "720p (1280×720)": (1280, 720),
    "1080p (1920×1080)": (1920, 1080),
}

# Global model cache — lazy load, keep at most one model in memory
_cached_model: Optional[Tuple[DepthAnythingV2, str]] = None  # (model, model_size_label)


# ---------------------------------------------------------------------------
# Device detection
# ---------------------------------------------------------------------------

def detect_device() -> Tuple[str, str]:
    """Return (torch_device_str, human_readable_description)."""
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0) or "NVIDIA GPU"
        return "cuda", f"CUDA — {name}"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps", "Apple Silicon (MPS)"
    return "cpu", "CPU (no GPU acceleration)"


# ---------------------------------------------------------------------------
# FFmpeg helpers
# ---------------------------------------------------------------------------

def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _get_ffmpeg_path() -> str:
    path = shutil.which("ffmpeg")
    if path is None:
        raise RuntimeError(
            "ffmpeg was not found on your system PATH.\n\n"
            "Install it first:\n"
            "  • macOS:  brew install ffmpeg\n"
            "  • Windows: winget install ffmpeg\n"
            "              …or download from https://ffmpeg.org/download.html\n"
            "Then restart this app."
        )
    return path


def _has_audio_stream(video_path: str) -> bool:
    ffmpeg = _get_ffmpeg_path()
    cmd = [
        ffmpeg, "-i", video_path,
        "-af", "volumedetect",
        "-vn", "-sn", "-dn",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return "Audio:" in result.stderr


def extract_audio(video_path: str, output_audio_path: str) -> bool:
    ffmpeg = _get_ffmpeg_path()
    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "aac",
        "-b:a", "192k",
        output_audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def write_video_ffmpeg(
    frames: np.ndarray,         # (N, H, W, 3) uint8 BGR
    fps: float,
    output_path: str,
    crf: int = 18,
) -> None:
    ffmpeg = _get_ffmpeg_path()
    _n, h, w, _c = frames.shape
    cmd = [
        ffmpeg, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", str(crf),
        "-preset", "medium",
        output_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    assert proc.stdin is not None
    try:
        proc.stdin.write(frames.tobytes())
        proc.stdin.close()
        proc.wait(timeout=300)
    except Exception:
        proc.kill()
        raise


def merge_audio_video(video_path: str, audio_path: str, output_path: str) -> None:
    ffmpeg = _get_ffmpeg_path()
    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, capture_output=True, check=True)


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------

def _download_with_progress(url: str, dest: Path, desc: str, progress) -> None:
    """Download a file with progress updates.  *progress* may be a gr.Progress or None."""

    dest.parent.mkdir(parents=True, exist_ok=True)

    def _report(count: int, block_size: int, total_size: int) -> None:
        if total_size > 0 and progress is not None:
            frac = min(count * block_size / total_size, 0.10)
            downloaded = count * block_size
            progress(frac, desc=f"{desc}  ({downloaded / 1e6:.0f} / {total_size / 1e6:.0f} MB)")

    if progress is not None:
        progress(0.0, desc=f"{desc}  connecting…")
    urlretrieve(url, str(dest), reporthook=_report)
    if progress is not None:
        progress(0.10, desc=f"{desc}  complete")


def _ensure_checkpoint(model_size_label: str, progress) -> Path:
    """Return the checkpoint path, downloading the model if not already present."""
    cfg = MODEL_DEFS[model_size_label]
    path = cfg["path"]

    if path.is_file():
        return path

    _download_with_progress(
        url=cfg["url"],
        dest=path,
        desc=f"Downloading {model_size_label}",
        progress=progress,
    )
    return path


def load_model(model_size_label: str, device_str: str, progress=None) -> DepthAnythingV2:
    """Return a loaded DepthAnythingV2 model, reusing cached instance when possible."""
    global _cached_model

    # Reuse cached model if the same size was already loaded
    if _cached_model is not None and _cached_model[1] == model_size_label:
        return _cached_model[0]

    cfg = MODEL_DEFS[model_size_label]
    checkpoint_path = _ensure_checkpoint(model_size_label, progress)

    # Unload previous model to free memory
    if _cached_model is not None:
        del _cached_model
        gc.collect()
        if device_str == "cuda":
            torch.cuda.empty_cache()

    device = torch.device(device_str)
    model = DepthAnythingV2(
        encoder=cfg["encoder"],
        features=cfg["features"],
        out_channels=cfg["out_channels"],
    )

    state_dict = torch.load(str(checkpoint_path), map_location="cpu", weights_only=True)
    model.load_state_dict(state_dict)
    model = model.to(device).eval()

    _cached_model = (model, model_size_label)
    return model


# ---------------------------------------------------------------------------
# Depth-to-grayscale conversion
# ---------------------------------------------------------------------------

def depth_to_grayscale(depth: np.ndarray, invert: bool = False) -> np.ndarray:
    """Normalize a float32 depth map to 0–255 uint8 grayscale."""
    d_min = depth.min()
    d_max = depth.max()
    if d_max - d_min < 1e-6:
        normalized = np.zeros_like(depth, dtype=np.uint8)
    else:
        normalized = ((depth - d_min) / (d_max - d_min) * 255).astype(np.uint8)

    if invert:
        normalized = 255 - normalized
    return normalized


# ---------------------------------------------------------------------------
# Temporal smoothing
# ---------------------------------------------------------------------------

class TemporalSmoother:
    """Exponential moving average across consecutive depth frames."""

    def __init__(self, alpha: float):
        self.alpha = alpha          # 1.0 = no smoothing, 0.05 = heavy
        self.previous: Optional[np.ndarray] = None

    def smooth(self, current: np.ndarray) -> np.ndarray:
        if self.previous is None:
            self.previous = current.copy()
            return current
        blended = self.alpha * current + (1.0 - self.alpha) * self.previous
        self.previous = blended.copy()
        return blended

    def reset(self) -> None:
        self.previous = None


# ---------------------------------------------------------------------------
# Main processing pipeline
# ---------------------------------------------------------------------------

def process_video(
    input_video_path: str,
    model_size_label: str,
    resolution_choice: str,
    invert_bw: bool,
    smoothing_strength: float,    # 0–100
    preserve_audio: bool,
    progress: gr.Progress = gr.Progress(),
) -> str:
    """Run the full depth-conversion pipeline.  Returns path to output MP4."""

    # ------------------------------------------------------------------
    # 0. Validate inputs
    # ------------------------------------------------------------------
    if not input_video_path:
        raise gr.Error("Please upload a video file first.")

    if not _ffmpeg_available():
        raise gr.Error(
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
        raise gr.Error(f"Could not open video file: {input_video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if total_frames < 1:
        cap.release()
        raise gr.Error("Video contains no frames.")

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
        progress(0.05, desc="Extracting original audio…")
        has_audio = _has_audio_stream(input_video_path)
        if has_audio:
            ok = extract_audio(input_video_path, str(audio_path))
            if not ok:
                has_audio = False

    # ------------------------------------------------------------------
    # 4. Read all frames into memory
    # ------------------------------------------------------------------
    progress(0.08, desc="Reading video frames…")
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
    progress(0.10, desc=f"Read {n_frames} frames  |  Starting depth inference…")

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
        progress(frac, desc=f"Depth inference  {idx + 1}/{n_frames}  |  {eta_str}")

        depth = model.infer_image(frame_bgr)   # returns float32 ndarray (H, W)
        depth_maps.append(depth)

    progress(0.80, desc="Depth inference complete  |  Post-processing…")

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
        progress(frac, desc=f"Applying smoothing  {idx + 1}/{n_frames}")
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
    progress(0.90, desc="Encoding output video (H.264 MP4)…")
    video_no_audio = os.path.join(tmp_dir, "depth_video.mp4")
    stacked = np.stack(output_frames, axis=0)
    write_video_ffmpeg(stacked, fps, video_no_audio)
    del stacked, output_frames
    gc.collect()

    # ------------------------------------------------------------------
    # 8. Mux audio
    # ------------------------------------------------------------------
    if has_audio and audio_path and os.path.exists(str(audio_path)):
        progress(0.95, desc="Merging original audio…")
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

    progress(1.0, desc="Done!")
    return output_file


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

CSS = """
.gradio-container { max-width: 720px !important; margin: 0 auto; }
.device-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.85em;
    font-weight: 600;
    margin: 8px 0;
}
.device-cuda { background: #76b900; color: #fff; }
.device-mps  { background: #0071e3; color: #fff; }
.device-cpu  { background: #e0e0e0; color: #333; }
"""


def create_ui() -> gr.Blocks:
    device_str, device_desc = detect_device()
    badge_class = {"cuda": "device-cuda", "mps": "device-mps"}.get(device_str, "device-cpu")
    device_html = f'<div class="device-badge {badge_class}">🖥  {device_desc}</div>'

    with gr.Blocks(css=CSS, title="Depth Video Converter") as demo:
        gr.Markdown(
            """# 🎥 Depth Video Converter
Convert any MP4 / MOV video into a **grayscale depth-map video**
using [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2).
            """
        )
        gr.HTML(device_html)

        with gr.Row():
            with gr.Column(scale=1):
                input_video = gr.Video(
                    label="Upload Video",
                    sources=["upload"],
                    format="mp4",
                )

                model_size = gr.Dropdown(
                    choices=list(MODEL_DEFS.keys()),
                    value="Small (fastest, ~95 MB)",
                    label="Model Size",
                    info="Larger models produce better depth maps but run slower.",
                )

                resolution = gr.Dropdown(
                    choices=list(RESOLUTION_PRESETS.keys()),
                    value="Original",
                    label="Output Resolution",
                    info="Downscale to speed up processing.",
                )

                invert = gr.Checkbox(
                    value=False,
                    label="Invert Black & White",
                    info="Swap near ↔ far.  Usually near = bright, far = dark.",
                )

                smoothing = gr.Slider(
                    minimum=0,
                    maximum=100,
                    value=60,
                    step=1,
                    label="Temporal Smoothing",
                    info="Higher values reduce flicker but may cause ghosting.",
                )

                preserve_audio = gr.Checkbox(
                    value=True,
                    label="Preserve Original Audio",
                    info="Copy the original audio track into the depth video (requires ffmpeg).",
                )

                process_btn = gr.Button("⚙ Process Video", variant="primary", size="lg")

            with gr.Column(scale=1):
                output_video = gr.Video(
                    label="Output Depth Video",
                    format="mp4",
                    autoplay=True,
                )

        process_btn.click(
            fn=process_video,
            inputs=[input_video, model_size, resolution, invert, smoothing, preserve_audio],
            outputs=output_video,
        )

        gr.Markdown(
            """---
### 📋 Tips
- Models are **auto-downloaded on first use** from Hugging Face.  Subsequent runs load from the local `models/` directory instantly.
- **Temporal smoothing** blends consecutive depth frames to reduce flicker.  Start at 60 and adjust.
- **Audio preservation** copies the original audio into the output.
- Everything runs **100 % locally** — nothing is uploaded anywhere.
            """
        )

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 58)
    print("  Depth Video Converter — Depth Anything V2 + Gradio")
    print("=" * 58)

    device_str, device_desc = detect_device()
    print(f"  Detected device : {device_desc}")

    ffmpeg_found = _ffmpeg_available()
    print(f"  ffmpeg          : {'✅ found' if ffmpeg_found else '❌ NOT FOUND'}")
    if not ffmpeg_found:
        print()
        print("  ⚠  ffmpeg is required for video encoding and audio handling.")
        print("     Install it before processing videos:")
        print("       macOS:   brew install ffmpeg")
        print("       Windows: winget install ffmpeg")
        print()

    # Check for model files
    print(f"  Models directory: {MODELS_DIR}")
    for label, cfg in MODEL_DEFS.items():
        p = cfg["path"]
        if p.is_file():
            status = f"✅ ({p.stat().st_size / 1e6:.0f} MB)"
        else:
            status = "⬇  auto-download on first use"
        print(f"    {status}  {label}")

    print(f"  Python          : {sys.version.split()[0]}")
    print(f"  PyTorch         : {torch.__version__}")
    print(f"  Gradio          : {gr.__version__}")
    print("=" * 58)
    print()

    demo = create_ui()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
