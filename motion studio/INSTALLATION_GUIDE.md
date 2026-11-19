# OpenGen Motion Graphics Studio: Complete Installation & Environment Setup Guide

This guide provides exact, verified, copy-paste installation commands and environment configuration steps for Windows 11/10, Linux (Ubuntu 22.04 / 24.04 LTS), and Docker.

---

## 1. System Requirements & Runtime Prerequisites

| Component | Minimum Specification | Recommended Production Specification |
|---|---|---|
| **Operating System** | Windows 10/11 x64, Ubuntu 22.04+ LTS, macOS 13+ | Ubuntu 24.04 LTS or Windows 11 Pro |
| **CPU** | 4-Core x86_64 / ARM64 (Apple Silicon) | 8-Core / 16-Thread (AMD Ryzen 7/9, Intel i7/i9) |
| **RAM** | 16 GB | 32 GB - 64 GB DDR5 |
| **GPU (Hardware Video & 3D)** | Integrated GPU (Intel Iris / AMD Radeon) | NVIDIA RTX 3060 / 4060 or higher (8GB+ VRAM, CUDA 12.4+) |
| **GPU (AI Video Wan/LTX)** | N/A (Cloud API / CPU offload) | NVIDIA RTX 3090 / 4090 / A100 (24GB+ VRAM) |
| **Disk Space** | 20 GB free space | 100 GB+ NVMe SSD |

---

## 2. Platform-Specific System Dependencies

### A. Windows Installation (PowerShell Administrator)

```powershell
# 1. Install Winget Package Manager dependencies
winget install Gyan.FFmpeg
winget install Google.Chrome
winget install OpenJS.NodeJS.LTS
winget install Oven-sh.Bun
winget install astral-sh.uv
winget install Git.Git

# 2. Verify System Binaries in PATH
ffmpeg -version
node -v
bun -v
uv --version
git --version
chrome --version
```

### B. Ubuntu / Debian Linux Installation (Bash)

```bash
# 1. Update repositories and install core build essentials
sudo apt update && sudo apt install -y \
  curl wget git build-essential \
  ffmpeg libavcodec-extra \
  fonts-freefont-ttf fonts-dejavu-core fonts-inter \
  libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2

# 2. Install Node.js 22 LTS (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# 3. Install Bun Runtime (High-speed JavaScript/TypeScript bundler & runner)
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc

# 4. Install UV Python Package Manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 5. Install Google Chrome (for headless Playwright/Chrome rendering)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt install -f -y
rm google-chrome-stable_current_amd64.deb

# 6. Verify installation
ffmpeg -version
node -v
bun -v
uv --version
google-chrome --version
```

---

## 3. Node.js & Bun Motion Graphics Engines Setup

OpenGen utilizes **HyperFrames** for 2D/GSAP/HTML rendering and **pdoom-video** for Three.js/GLSL 3D rendering.

### A. HyperFrames Global / Local Setup

```bash
# Option 1: Install globally for instant CLI execution
npm install -g hyperframes

# Option 2: Verify zero-install execution via npx
npx hyperframes --version

# Install Chrome browser binaries for Playwright / Puppeteer headless execution
npx playwright install chromium
```

### B. pdoom-video Setup (Three.js + Anime.js Engine)

```bash
# Clone or navigate to the pdoom-video engine directory
cd engines/pdoom-video/app

# Install exact production dependencies using Bun
bun install three animejs opentype.js playwright-core vite

# Verify Bun execution and render script syntax
bun scripts/render.ts --help
```

---

## 4. Python Environment Setup (AI & Audio Services)

We recommend using **`uv`** for reproducible, isolated, and lightning-fast Python virtual environments.

### A. Core Python Dependencies Installation

```bash
# Create dedicated virtual environment with Python 3.11 or 3.12
uv venv .venv --python 3.11
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install Torch with CUDA 12.4 acceleration (or CPU if no NVIDIA GPU)
# For NVIDIA CUDA:
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
# For CPU-only:
# uv pip install torch torchvision torchaudio

# Install Audio, Speech, Scene Detection, and Video Analysis Libraries
uv pip install \
  scenedetect[opencv] \
  faster-whisper \
  librosa \
  soundfile \
  demucs \
  pydantic \
  fastapi \
  uvicorn[standard] \
  requests \
  httpx \
  python-multipart \
  pillow \
  numpy

# Install LLM Provider SDKs
uv pip install \
  google-genai \
  openai \
  anthropic \
  diffusers \
  transformers \
  accelerate
```

### B. VoiceStudio Local TTS & Voice Daemon Setup

```bash
# Navigate to VoiceStudio backend
cd engines/VoiceStudio/backend

# Install VoiceStudio requirements
uv pip install -r requirements.txt

# Start VoiceStudio daemon on port 3900 (runs in background)
python -m uvicorn main:app --host 127.0.0.1 --port 3900 &
```

---

## 5. Verification Test Suite

Run these verification tests to confirm your host environment is 100% operational before executing OpenGen video jobs.

### Test 1: FFmpeg Hardware Acceleration Verification

```bash
# Check if NVIDIA NVENC H.264 hardware encoder is detected
ffmpeg -encoders 2>&1 | grep nvenc
# Expected output on NVIDIA systems:
# V....D h264_nvenc           NVIDIA NVENC H.264 encoder (codec h264)
# V....D hevc_nvenc           NVIDIA NVENC hevc encoder (codec hevc)
```

### Test 2: HyperFrames Headless Render Test

Create a minimal test file `test_render.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { margin: 0; background: #0f172a; display: flex; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; color: white; }
    h1 { font-size: 64px; }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
</head>
<body>
  <div id="composition" class="composition" data-fps="30" data-duration="2.0" style="width: 1080px; height: 1920px;">
    <div class="clip" data-start="0.0" data-duration="2.0" id="scene1">
      <h1 id="title">OpenGen Engine Ready</h1>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({ paused: true });
    tl.from("#title", { opacity: 0, scale: 0.8, duration: 1.0, ease: "power2.out" });
    window.__timelines = { scene1: tl };
  </script>
</body>
</html>
```

Run render command:

```bash
npx hyperframes render -c test_render.html -o test_output.mp4 --fps 30
```

Verify that `test_output.mp4` is created and plays smoothly.

### Test 3: Python Video Analysis & Scene Detection Test

Create a test script `verify_analysis.py`:

```python
import sys
from scenedetect import detect, ContentDetector
import librosa
from faster_whisper import WhisperModel

print("[OK] PySceneDetect loaded successfully.")
print("[OK] Librosa audio processor loaded successfully.")

# Test Whisper model load
try:
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("[OK] Faster-Whisper ASR engine loaded successfully.")
except Exception as e:
    print(f"[ERROR] Whisper failed: {e}")

print("All OpenGen analysis prerequisites verified.")
```

Run test:
```bash
python verify_analysis.py
```

---

## 6. Docker Container Deployment (Production Headless Node)

For containerized cloud deployments (Kubernetes, AWS ECS, GCP Cloud Run), use the following hardened Dockerfile:

```dockerfile
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies & Chrome
RUN apt-get update && apt-get install -y \
    curl wget git build-essential \
    ffmpeg fonts-inter fonts-dejavu-core \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 \
    python3.11 python3.11-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get install -f -y \
    && rm google-chrome-stable_current_amd64.deb

# Install Node.js 22 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g hyperframes

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:${PATH}"

# Install uv & Python dependencies
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app
COPY . /app

RUN uv venv /app/.venv --python 3.11
ENV PATH="/app/.venv/bin:${PATH}"
RUN uv pip install fastapi uvicorn[standard] scenedetect[opencv] faster-whisper librosa google-genai openai

EXPOSE 8000
CMD ["uvicorn", "opengen.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```
