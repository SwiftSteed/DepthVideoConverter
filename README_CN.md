<p align="right">
  <a href="README.md">EN</a> | <sub>中文</sub>
</p>

<h1 align="center">Depth Video Converter</h1>

<p align="center">
  使用 <a href="https://github.com/DepthAnything/Depth-Anything-V2">Depth Anything V2</a>
  将任意视频转换为<strong>灰度深度图视频</strong>。
  全部本地运行，无需联网上传。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
</p>

---

## 目录

- [它能做什么？](#它能做什么)
- [功能特性](#功能特性)
- [桌面应用](#桌面应用)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [使用说明](#使用说明)
- [控制参数](#控制参数)
- [模型选择](#模型选择)
- [工作原理](#工作原理)
- [常见问题](#常见问题)
- [参与贡献](#参与贡献)
- [许可证](#许可证)
- [致谢](#致谢)

---

## 它能做什么？

对视频的每一帧进行**单目深度估计**，输出**深度图视频**——画面中每个像素的亮度表示该点到相机的距离。

底层模型为 [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2)，一个单目深度估计基础模型（NeurIPS 2024）。全程本地运行。

### 效果演示

| 原始视频 | 深度图视频（Large 模型） |
|---|---|
| [🎬 `examples/original.mp4`](examples/original.mp4) | [🎬 `examples/depth_large.mp4`](examples/depth_large.mp4) |

> 点击上方链接下载对比。深度视频使用 **Large** 模型生成——近处物体偏亮，远处物体偏暗。

---

## 功能特性

- **Web 界面** — 基于 Gradio，拖拽上传，无需命令行
- **三种模型尺寸** — Small（~95 MB）、Base（~372 MB）、Large（~1.2 GB）
- **自动 GPU 检测** — Windows 上使用 NVIDIA CUDA，Mac 上使用 Apple Silicon (MPS)，其他回退到 CPU
- **分辨率预设** — 原始 / 480p / 720p / 1080p
- **黑白翻转** — 一键交换近远关系
- **时序平滑** — 相邻帧指数移动平均，消除闪烁
- **音频保留** — 将原始音轨重新封装到输出 MP4 中（需 ffmpeg）
- **H.264 MP4 输出** — 浏览器、QuickTime、VLC、社交平台均可播放

---

## 桌面应用

基于 **Tauri**（Rust + React）的原生桌面应用 — 与 [Shuttle](https://github.com/litlifesoftware/shuttle) 完全一致的技术栈。双击启动，无需终端。

<p align="center">
  <sub><i>拖拽上传、参数面板、实时进度 — 和 Web 版完全相同的功能</i></sub>
</p>

### 工作原理

桌面壳仅负责 UI 显示。所有 AI 推理（PyTorch + Depth Anything V2）仍由 Python 以本地 FastAPI 服务形式运行：

```
桌面应用 (Tauri + React)  ──HTTP──▶  Python 侧载服务 (FastAPI :9876)
       ↓                                         ↓
  原生窗口                                  depth_converter
  (15 MB .dmg)                              (PyTorch + ffmpeg)
```

### 快速开始

```bash
# 在项目根目录：

# 1. 启动 Python 侧载服务
python -m server.main

# 2. 在另一终端，启动桌面开发模式
cd desktop
npm install
npm run tauri dev
```

### 打包

```bash
cd desktop
npm run tauri build    # → .dmg (macOS) / .msi (Windows) / .deb + .AppImage (Linux)
```

> **注意：** 打包后的应用需要用户系统已安装 Python 3.10+ 和 ffmpeg。
> 后续版本将内置独立 Python 发行版，实现真正的一键安装。

---

## 环境要求

| 需求 | 用途 | 安装方式 |
|---|---|---|
| **Python 3.10+** | 应用运行环境 | [python.org](https://www.python.org/downloads/) |
| **ffmpeg** | 视频编码与音频封装 | `brew install ffmpeg`（Mac）/ `winget install ffmpeg`（Win） |
| **模型权重** | Depth Anything V2 权重 | 首次使用时从 Hugging Face 自动下载，缓存在 `models/` |

其余依赖由 `pip install -r requirements.txt` 自动安装。

### 模型权重

首次选择模型时自动下载，缓存在 `models/` 目录：

```
models/
├── depth_anything_v2_vits.pth   # 95 MB  — Small
├── depth_anything_v2_vitb.pth   # 372 MB — Base
└── depth_anything_v2_vitl.pth   # 1.2 GB — Large
```

也可以从 [Hugging Face](https://huggingface.co/depth-anything) 手动下载放入 `models/`。

---

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/SwiftSteed/DepthVideoConverter.git
cd DepthVideoConverter

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\Activate.ps1       # Windows PowerShell

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 启动
python depth_video_converter.py
```

在浏览器中打开 **http://127.0.0.1:7860**，上传视频，点击 **Process**。

> **Windows + NVIDIA GPU？** 建议先安装 CUDA 版 PyTorch 以获得最佳性能：
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
> ```
> 然后再执行 `pip install -r requirements.txt`。

---

## 使用说明

1. 启动应用：`python depth_video_converter.py`
2. 在浏览器中打开终端打印的地址（默认：`http://127.0.0.1:7860`）
3. 上传 **MP4** 或 **MOV** 视频
4. 选择参数（参见[控制参数](#控制参数)）
5. 点击 **Process Video**
6. 观察进度条——模型从本地 `models/` 目录加载，零网络延迟
7. 下载或播放输出视频

---

## 控制参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| **Model Size** | Small | 更大的模型 → 更好的深度图，更慢的推理速度 |
| **Output Resolution** | Original | 降分辨率可加速处理（480p / 720p / 1080p） |
| **Invert Black & White** | 关闭 | 默认：近处亮、远处暗。勾选后翻转 |
| **Temporal Smoothing** | 60 | 0 = 不平滑。100 = 强平滑（减少闪烁，但可能有拖影） |
| **Preserve Original Audio** | 开启 | 将原始音轨复制到输出视频中。需要 ffmpeg |

---

## 模型选择

| 模型 | 文件大小 | 参数量 | 质量 | 适用场景 |
|---|---|---|---|---|
| **Small** (vits) | 95 MB | 24.8M | ⭐⭐ | 快速预览、长视频 |
| **Base** (vitb) | 372 MB | 97.5M | ⭐⭐⭐ | 日常使用——最推荐的甜点 |
| **Large** (vitl) | 1.2 GB | 335.3M | ⭐⭐⭐⭐ | 最佳画质、短视频 |

### 实测基准

测试设备：**Mac mini (Mac16,10)** — **Apple M4，10 核（4P + 6E），24 GB 内存**，
macOS 15，PyTorch 2.x + MPS 后端。输入：720×1280 竖屏视频，15 秒（450 帧），时序平滑 60：

| 模型 | 帧率 | 总耗时 | 相对 Small |
|---|---|---|---|
| **Small** | 5.0 fps | 1.5 分钟 | 1× |
| **Base** | 2.1 fps | 3.6 分钟 | 慢 2.4× |
| **Large** | 0.69 fps | 10.8 分钟 | 慢 7.2× |

### 推荐

| 场景 | 选择 |
|---|---|
| "只是想看看效果" | **Small** — 15 秒视频只需 1.5 分钟 |
| 日常主力，平衡之选 | **Base** — 慢 2.4 倍，深度质量显著提升 |
| 最终成品，追求最佳质量 | **Large** — 慢 7 倍，但边缘和层次明显更锐利 |

> **关键结论：** Base 是最佳甜点。只比 Small 慢 2.4 倍，但深度图质量非常接近 Large。
> Large 适合短而重要的片段，每一处细节都值得等待。

---

## 工作原理

```
  输入视频 (.mp4 / .mov)
        │
        ▼
  ┌─────────────────┐
  │  读取帧          │  OpenCV VideoCapture
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Depth Anything  │  PyTorch 逐帧推理
  │  V2 模型         │  → float32 深度图
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  时序 EMA 平滑   │  与前一帧混合
  │                  │  → 减少闪烁
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  归一化 +        │  0–255 灰度
  │  黑白翻转（可选）│
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  ffmpeg 编码     │  H.264 (libx264) MP4
  │  + 音频封装      │  ← 原始音轨
  └────────┬────────┘
           │
           ▼
  输出视频 (.mp4)
```

---

## 常见问题

### 需要 GPU 吗？

不需要。CPU、MPS（Apple Silicon）、CUDA（NVIDIA）均可运行。应用会自动检测可用设备。

### 需要多长时间？

实测数据来自 **Mac mini (Mac16,10) — Apple M4，10 核（4P + 6E），24 GB 内存**，
macOS 15，PyTorch MPS 后端。720×1280，15 秒视频。CUDA 会更快，CPU 会更慢。

| 模型 | 帧率 | 15s 视频 | 30s 视频 | 60s 视频 |
|---|---|---|---|---|
| **Small** | 5.0 fps | 1.5 分钟 | 3 分钟 | 6 分钟 |
| **Base** | 2.1 fps | 3.6 分钟 | 7 分钟 | 14 分钟 |
| **Large** | 0.69 fps | 10.8 分钟 | 22 分钟 | 43 分钟 |

**其他硬件大致倍率**（相对 Apple M4 MPS）：

| 硬件 | 相对 M4 MPS 速度 |
|---|---|
| NVIDIA RTX 4090 | 快 3–4 倍 |
| NVIDIA RTX 3060/4060 | 快 2 倍 |
| Apple M1/M2 | 0.8–0.9 倍 |
| 现代 CPU (x86) | 0.3–0.5 倍 |

将上表数据乘以对应倍率即可估算你设备上的耗时。

### 显存不足（CUDA out of memory）

换用更小的模型（Small）或降低输出分辨率。也可以限制 PyTorch 内存分配：

```bash
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
```

### Apple Silicon 显示 "CPU" 而非 "MPS"

确保安装了支持 MPS 的 PyTorch（2.1+）：

```bash
python -c "import torch; print(torch.backends.mps.is_available())"
```

如果输出 `False`，重新安装：

```bash
pip install torch --upgrade
```

### 找不到 ffmpeg

安装并确保其位于 PATH 中：

- **macOS：** `brew install ffmpeg`
- **Windows：** `winget install ffmpeg` 或从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载

---

## 参与贡献

欢迎提交 Bug 报告、功能请求和 Pull Request。

1. Fork 本仓库
2. 创建分支（`git checkout -b feat/my-feature`）
3. 做出修改
4. 提交清晰的 PR 描述

请保持代码风格与现有代码一致（PEP 8，所有函数签名使用类型注解）。

---

## 许可证

本项目使用 **MIT 许可证**——详见源码文件。

Depth Anything V2 来自 [DepthAnything](https://github.com/DepthAnything/Depth-Anything-V2)
项目，采用 **Apache 2.0 许可证**。

---

## 致谢

- [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2) —
  驱动此工具的出色深度估计模型。`depth_anything_v2/` 中 vendored 的模型架构代码来自官方仓库（Apache 2.0）。
- [Gradio](https://www.gradio.app/) — 简洁高效的 Web UI 框架
- [OpenCV](https://opencv.org/) — 视频 I/O 与图像处理
- [ffmpeg](https://ffmpeg.org/) — 可靠的 H.264 编码与音频封装
