<p align="right">
  <sub>EN</sub> | <a href="README_CN.md">中文</a>
</p>

<h1 align="center">Depth Video Converter</h1>

<p align="center">
  Turn any video into a <strong>grayscale depth-map video</strong> using
  <a href="https://github.com/DepthAnything/Depth-Anything-V2">Depth Anything V2</a>.
  Everything runs locally.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## Demo

| Original | Depth Map (Large model) |
|---|---|
| [🎬 `examples/original.mp4`](examples/original.mp4) | [🎬 `examples/depth_large.mp4`](examples/depth_large.mp4) |

> Near = bright, far = dark. Generated with the **Large** model.

---

## Quick Start

```bash
# Prerequisites: Python 3.10+ and ffmpeg
#   macOS:   brew install ffmpeg
#   Windows: winget install ffmpeg

git clone https://github.com/SwiftSteed/DepthVideoConverter.git
cd DepthVideoConverter
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
python depth_video_converter.py
```

Open **http://127.0.0.1:7860**, upload a video, click **Process**.

Models are auto-downloaded on first use from Hugging Face (cached in `models/`).

> **NVIDIA GPU?** For CUDA acceleration:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
> ```
> Then `pip install -r requirements.txt`.

---

## Controls

| Control | Default | What it does |
|---|---|---|
| **Model Size** | Small | Small (~95 MB) / Base (~372 MB) / Large (~1.2 GB). Larger = better quality, slower. |
| **Output Resolution** | Original | Downscale to speed up processing (480p / 720p / 1080p). |
| **Invert Black & White** | Off | Swap near ↔ far. |
| **Temporal Smoothing** | 60 | 0 = off. 100 = max (less flicker, possible ghosting). |
| **Preserve Original Audio** | On | Copy the original audio track into output. |

### Model performance (Apple M4 MPS, 720×1280, 15s clip)

| Model | Speed | 15s clip | 60s clip |
|---|---|---|---|
| **Small** | 5.0 fps | 1.5 min | 6 min |
| **Base** | 2.1 fps | 3.6 min | 14 min |
| **Large** | 0.7 fps | 10.8 min | 43 min |

Base is the sweet spot. CUDA is ~2–4× faster depending on GPU.

---

## License

MIT. [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) is Apache 2.0.

Models from [depth-anything](https://huggingface.co/depth-anything) on Hugging Face.
Built with [Gradio](https://www.gradio.app/), [OpenCV](https://opencv.org/), [ffmpeg](https://ffmpeg.org/).
