<p align="right">
  <a href="README.md">EN</a> | <sub>中文</sub>
</p>

<h1 align="center">Depth Video Converter</h1>

<p align="center">
  使用 <a href="https://github.com/DepthAnything/Depth-Anything-V2">Depth Anything V2</a>
  将任意视频转换为<strong>灰度深度图视频</strong>。
  全程本地运行。
</p>

<p align="center">
  <a href="https://huggingface.co/spaces/SwiftSteed/depth-video-converter"><img src="https://img.shields.io/badge/🤗-在%20HF%20Spaces%20试用-blue" alt="HF Spaces"></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## 效果演示

| 原始视频 | 深度图（Large 模型） |
|---|---|
| [🎬 `examples/original.mp4`](examples/original.mp4) | [🎬 `examples/depth_large.mp4`](examples/depth_large.mp4) |

> 近处偏亮，远处偏暗。使用 **Large** 模型生成。

---

## 快速开始

### Docker（推荐）

```bash
git clone https://github.com/SwiftSteed/DepthVideoConverter.git
cd DepthVideoConverter
docker compose up
```

浏览器打开 **http://localhost:7860**。搞定。无需安装 Python、ffmpeg、PyTorch——一切都在容器内运行。

> **NVIDIA GPU？** compose 文件自动启用 GPU。
> 需先安装 [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。
>
> **Apple Silicon / 无 GPU？** 自动回退 CPU 模式，慢但能用 Small 模型快速预览。

### 本地（Python）

```bash
# 前提：Python 3.10+ 和 ffmpeg
#   macOS:   brew install ffmpeg
#   Windows: winget install ffmpeg

git clone https://github.com/SwiftSteed/DepthVideoConverter.git
cd DepthVideoConverter
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
python depth_video_converter.py
```

浏览器打开 **http://127.0.0.1:7860**，上传视频，点击 **Process**。

模型首次使用时自动从 Hugging Face 下载，缓存在 `models/` 目录。

> **NVIDIA GPU？** 安装 CUDA 版 PyTorch 以获得更佳性能：
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
> ```
> 再执行 `pip install -r requirements.txt`。

---

## 参数说明

| 参数 | 默认值 | 说明 |
|---|---|---|
| **Model Size** | Small | Small (~95 MB) / Base (~372 MB) / Large (~1.2 GB)。越大质量越好，越慢。 |
| **Output Resolution** | Original | 降分辨率可加速（480p / 720p / 1080p）。 |
| **Invert Black & White** | 关闭 | 翻转近远关系。 |
| **Temporal Smoothing** | 60 | 0 = 关闭。100 = 最大（减少闪烁，可能拖影）。 |
| **Preserve Original Audio** | 开启 | 将原始音轨复制到输出。 |

### 模型性能（Apple M4 MPS, 720×1280, 15 秒视频）

| 模型 | 速度 | 15s 视频 | 60s 视频 |
|---|---|---|---|
| **Small** | 5.0 fps | 1.5 分钟 | 6 分钟 |
| **Base** | 2.1 fps | 3.6 分钟 | 14 分钟 |
| **Large** | 0.7 fps | 10.8 分钟 | 43 分钟 |

Base 是推荐之选。CUDA 会比 MPS 快约 2–4 倍。

---

## 许可证

MIT。[Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) 使用 Apache 2.0。

模型来自 Hugging Face [depth-anything](https://huggingface.co/depth-anything)。
基于 [Gradio](https://www.gradio.app/)、[OpenCV](https://opencv.org/)、[ffmpeg](https://ffmpeg.org/) 构建。
