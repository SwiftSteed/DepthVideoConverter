<p align="right">
  <sub>EN</sub> | <a href="README_CN.md">中文</a>
</p>

<h1 align="center">Depth Video Converter</h1>

<p align="center">
  Turn any video into a <strong>grayscale depth-map video</strong> using
  <a href="https://github.com/DepthAnything/Depth-Anything-V2">Depth Anything V2</a>.
  Everything runs locally — no cloud uploads.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
</p>

---

## Table of Contents

- [What does it do?](#what-does-it-do)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Controls](#controls)
- [Model Sizes](#model-sizes)
- [How It Works](#how-it-works)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## What does it do?

This tool applies **monocular depth estimation** to every frame of a video, producing a **depth map video** — a grayscale output where each pixel's brightness encodes its distance from the camera.

Powered by [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2), a foundation model for monocular depth estimation (NeurIPS 2024). Everything runs locally.

---

## Features

- **Web UI** — Gradio interface with drag-and-drop upload, no CLI needed
- **Three model sizes** — Small (~100 MB), Base (~400 MB), Large (~1.3 GB)
- **Auto GPU detection** — NVIDIA CUDA on Windows, Apple Silicon (MPS) on Mac, CPU fallback
- **Resolution presets** — original / 480p / 720p / 1080p
- **Black & white inversion** — swap near ↔ far in one click
- **Temporal smoothing** — exponential moving average between consecutive frames to kill flicker
- **Audio preservation** — re-mux the original audio track into the output MP4 (via ffmpeg)
- **H.264 MP4 output** — plays everywhere: browsers, QuickTime, VLC, social media

---

## Prerequisites

| What | Why | How |
|---|---|---|
| **Python 3.10+** | The app runtime | [python.org](https://www.python.org/downloads/) |
| **ffmpeg** | Video encoding & audio muxing | `brew install ffmpeg` (Mac) / `winget install ffmpeg` (Win) |
| **Model checkpoints** | Depth Anything V2 weights | Download `.pth` files from [GitHub Releases](https://github.com/DepthAnything/Depth-Anything-V2/releases) → place in `models/` |

Everything else is installed by `pip install -r requirements.txt`.

### Downloading model checkpoints

Download the `.pth` files from the [official releases page](https://github.com/DepthAnything/Depth-Anything-V2/releases)
and place them in the `models/` directory:

```
models/
├── depth_anything_v2_vits.pth   # 95 MB  — Small
├── depth_anything_v2_vitb.pth   # 372 MB — Base
└── depth_anything_v2_vitl.pth   # 1.2 GB — Large
```

You only need the model(s) you plan to use. The app will show which files are
present on startup.

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/SwiftSteed/DepthVideoConverter.git
cd DepthVideoConverter

# 2. Download model checkpoints (pick at least one)
#    → https://github.com/DepthAnything/Depth-Anything-V2/releases
#    Place the .pth files in the models/ directory.

# 3. Create a virtual environment
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\Activate.ps1       # Windows PowerShell

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Launch
python depth_video_converter.py
```

Open **http://127.0.0.1:7860** in your browser, upload a video, and hit
**Process**.

> **NVIDIA GPU on Windows?**  Install CUDA-enabled PyTorch first for best
> performance:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
> ```
> Then run `pip install -r requirements.txt`.

---

## Usage

1. Launch the app: `python depth_video_converter.py`
2. Open the URL printed in the terminal (default: `http://127.0.0.1:7860`)
3. Upload an **MP4** or **MOV** video
4. Choose your settings (see [Controls](#controls))
5. Click **Process Video**
6. Watch the progress bar — models are loaded from local `models/` directory,
   so there's zero network delay
7. Download or play the output video

---

## Controls

| Control | Default | What it does |
|---|---|---|
| **Model Size** | Small | Bigger model → better depth maps, slower inference |
| **Output Resolution** | Original | Downscale for faster processing (480p / 720p / 1080p) |
| **Invert Black & White** | Off | Default: near = bright, far = dark. Flip it with this. |
| **Temporal Smoothing** | 60 | 0 = no smoothing. 100 = heavy smoothing (less flicker, possible ghosting). |
| **Preserve Original Audio** | On | Copies the audio track from the input into the output. Requires ffmpeg. |

---

## Model Sizes

| Model | File | Params | Quality | Best for |
|---|---|---|---|---|
| **Small** (vits) | 95 MB | 24.8M | ⭐⭐ | Quick previews, long videos |
| **Base** (vitb) | 372 MB | 97.5M | ⭐⭐⭐ | Everyday use — the sweet spot |
| **Large** (vitl) | 1.2 GB | 335.3M | ⭐⭐⭐⭐ | Best quality, short clips |

### Real-world benchmarks

Tested on a **Mac mini (Mac16,10)** — **Apple M4, 10-core (4P + 6E), 24 GB RAM**,
macOS 15, PyTorch 2.x with MPS backend.  Input: 720×1280 portrait video,
15 seconds (450 frames), temporal smoothing at 60:

| Model | FPS | Total time | × vs Small |
|---|---|---|---|
| **Small** | 5.0 fps | 1.5 min | 1× |
| **Base** | 2.1 fps | 3.6 min | 2.4× slower |
| **Large** | 0.69 fps | 10.8 min | 7.2× slower |

### Recommendation

| Use case | Pick |
|---|---|
| "Just want to see what it looks like" | **Small** — 1.5 min for a 15s clip |
| Daily driver, good balance | **Base** — 2.4× slower, noticeably better depth |
| Final output, maximum quality | **Large** — 7× slower, but edges and layering are visibly sharper |

> **Key insight:** Base hits the sweet spot. It's only 2.4× slower than Small
> but produces depth maps much closer to Large quality. Large is worth it for
> short, important clips where every detail counts.

---

## How It Works

```
  Input (.mp4 / .mov)
        │
        ▼
  ┌─────────────────┐
  │  Frame reader    │  OpenCV VideoCapture
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Depth Anything  │  PyTorch inference per frame
  │  V2 model        │  → float32 depth map
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Temporal EMA    │  Blend with previous frame
  │  smoothing       │  → reduces flicker
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Normalize +     │  0–255 grayscale
  │  B/W invert      │  (optional)
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  ffmpeg encode   │  H.264 (libx264) MP4
  │  + audio mux     │  ← original audio track
  └────────┬────────┘
           │
           ▼
  Output (.mp4)
```

---

## FAQ

### Do I need a GPU?

No.  It runs on CPU, MPS (Apple Silicon), or CUDA (NVIDIA).
The app auto-detects whatever is available.

### How long does it take?

Real numbers from a **Mac mini (Mac16,10) — Apple M4, 10-core (4P+6E), 24 GB RAM**,
macOS 15, PyTorch MPS backend.  720×1280, 15-second clip. Expect CUDA to be
faster and CPU to be slower.

| Model | FPS | 15s clip | 30s clip | 60s clip |
|---|---|---|---|---|
| **Small** | 5.0 fps | 1.5 min | 3 min | 6 min |
| **Base** | 2.1 fps | 3.6 min | 7 min | 14 min |
| **Large** | 0.69 fps | 10.8 min | 22 min | 43 min |

**Rough multipliers** for other hardware (vs. Apple M4 MPS):

| Hardware | Speed vs M4 MPS |
|---|---|
| NVIDIA RTX 4090 | ~3–4× faster |
| NVIDIA RTX 3060/4060 | ~2× faster |
| Apple M1/M2 | ~0.8–0.9× |
| Modern CPU (x86) | ~0.3–0.5× |

Multiply the table above by these factors for a rough estimate on your
machine.

### "CUDA out of memory"

Switch to a smaller model (Small) or lower output resolution.  You can also
limit the memory PyTorch allocates:

```bash
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
```

### Apple Silicon shows "CPU" instead of "MPS"

Make sure PyTorch was built with MPS support (2.1+):

```bash
python -c "import torch; print(torch.backends.mps.is_available())"
```

If it prints `False`, reinstall:

```bash
pip install torch --upgrade
```

### "ffmpeg was not found"

Install it and make sure it's on your PATH:

- **macOS:** `brew install ffmpeg`
- **Windows:** `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)

---

## Contributing

Bug reports, feature requests, and pull requests are welcome.

1. Fork the repo
2. Create a branch (`git checkout -b feat/my-feature`)
3. Make your changes
4. Open a PR with a clear description

Please keep the code consistent with the existing style (PEP 8, type hints on
all function signatures).

---

## License

This project is licensed under the **MIT License** — see the source file for
details.

Depth Anything V2 is from the [DepthAnything](https://github.com/DepthAnything/Depth-Anything-V2)
project and is available under the **Apache 2.0 License**.

---

## Acknowledgments

- [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) —
  the incredible depth estimation model that powers this tool. The vendored
  model architecture code in `depth_anything_v2/` comes from the official repo
  (Apache 2.0).
- [Gradio](https://www.gradio.app/) — for the dead-simple web UI framework
- [OpenCV](https://opencv.org/) — video I/O and image processing
- [ffmpeg](https://ffmpeg.org/) — reliable H.264 encoding and audio muxing
