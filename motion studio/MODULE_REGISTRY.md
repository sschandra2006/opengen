# MODULE REGISTRY: AI VIDEO PRODUCTION STUDIO

This document registers all modules available in the studio workspace (`f:\motion graphics\motion studio`), detailing their capabilities, entry points, communication interfaces, runtime requirements, and operational status.

---

## 1. STUDIO MODULE SUMMARY TABLE

| Module | Core Capabilities | Primary Entry Point | Interface | Key Dependencies | Status |
|---|---|---|---|---|---|
| **HyperFrames** (`./hyperframes`) | HTML/CSS/GSAP composition, WebGL transitions, multi-track audio, LUFS normalization, Remotion migration | `npx hyperframes` or `packages/cli/bin/hyperframes.mjs` | CLI (`init`, `preview`, `render`, `audio`), Dev Server (port 3002) | Node.js >=22, FFmpeg, Headless Chrome | **READY** (Global CLI active via npx) |
| **pdoom-video** (`./pdoom-video`) | Deterministic Three.js 3D rendering, Anime.js motion, opentype plotter typography, GLSL bloom/grain post-fx, CTC/Whisper forced audio alignment | `pdoom-video/app/scripts/render.ts` | CLI (`bun scripts/render.ts [video\|stills\|sheet]`), Vite dev server (port 5173) | Bun, Three.js, Anime.js, Playwright-core, FFmpeg, Chrome | **READY** (`node_modules` pre-installed, Bun & Chrome available) |
| **VoiceStudio** (`./VoiceStudio`) | AI voice cloning, multilingual TTS (OmniVoice, Kokoro), ASR transcription (Whisper.cpp), SFX generation, dubbing | `VoiceStudio/backend/main.py` & `cli/` | REST API (FastAPI port 3900), OpenAI-compatible `/v1/audio/speech`, CLI, Docker | Python >=3.11, PyTorch, CUDA, FastAPI, Gradio | **READY / SERVER** (Host has Python 3.13, CUDA 13.3, RTX 3050; Docker image available) |
| **raea** (`./raea`) | Native GPU-accelerated React/TSX video composition, Bevy 0.20 ECS 3D engine, WGPU shaders, automated video quality checks | `raea.exe` (via PowerShell installer) | CLI (`raea render`, `raea play`, `raea check`) | Rust / Bevy, DirectX 12 / Vulkan, VC++ Redistributable | **CANARY / OPTIONAL** (Source in repo; binary installable on demand via `install.ps1`) |

---

## 2. DETAILED MODULE PROFILES

### Module 1: HyperFrames (`./hyperframes`)
- **Repository**: `heygen-com/hyperframes`
- **Location**: `f:\motion graphics\motion studio\hyperframes`
- **Primary Purpose**:
  - Turns declarative HTML5, CSS animations, and GSAP timelines into deterministic MP4 videos.
  - Zero-React alternative to Remotion, eliminating virtual DOM overhead and complex bundlers.
  - Built-in audio analysis for onset/hit detection, beat extraction, and EBU R128 (-14 LUFS) volume normalization.
  - Native Remotion conversion skill (`skills/remotion-to-hyperframes`).
- **Entry Points**:
  - Global CLI: `npx hyperframes`
  - Studio Preview: `npx hyperframes preview --port 3002`
  - Render: `npx hyperframes render -c <html_file> -o <output.mp4>`
  - Audio tools: `npx hyperframes audio <audio_file>`, `npx hyperframes beats <audio_file>`
  - Local TTS: `npx hyperframes tts "<text>" -o <output.mp3>`
- **Interface Protocol**:
  - CLI arguments and stdout/stderr JSON diagnostics (`@hf-diagnostic`, `@hf-result`).
  - Standard HTML/CSS/JS file inputs with `data-composition-*` attributes.
- **Dependencies**:
  - Node.js `v26.7.0` (Host satisfied)
  - FFmpeg `9.0.2` (Host satisfied)
  - Google Chrome (Host satisfied)
- **Status**: Production-ready. Can be executed immediately from workspace root.

---

### Module 2: pdoom-video (`./pdoom-video`)
- **Repository**: `pdoom-video`
- **Location**: `f:\motion graphics\motion studio\pdoom-video`
- **Primary Purpose**:
  - Deterministic 3D and 2D motion graphics rendering engine.
  - Three.js scenes with custom camera tracks, PBR lighting, and particle effects.
  - Anime.js v4 animations for complex mathematical easings and kinetic transitions.
  - Single-stroke plotter fonts and vector text wipes using `opentype.js`.
  - GLSL post-processing pass: bloom, halation, film grain, and chromatic aberration.
  - Audio synchronization engine:
    - Reads `data/lyrics.json` (word and syllable level timestamps).
    - Reads `data/audio.json` (BPM, beats, downbeats, low/mid/high energy, drums, vocals).
  - Python audio analysis suite (`pdoom-video/analysis`): Demucs stem separation, Whisper CTC forced alignment, and beat tracker.
- **Entry Points**:
  - Video Renderer: `pdoom-video/app/scripts/render.ts`
  - Vite Live Preview: `pdoom-video/app` -> `bunx vite` (port 5173)
  - Analysis suite: `pdoom-video/analysis/align.py`, `pdoom-video/analysis/analyze.py`
- **Interface Protocol**:
  - Bun CLI scripts with flags (`--from`, `--to`, `--fps`, `--scale`, `--landscape`, `--out`, `--only`).
  - Data ingestion via standard JSON files (`lyrics.json`, `audio.json`).
  - Scene creation via TypeScript classes extending `Scene` in `src/scenes/`.
- **Dependencies**:
  - Bun `1.4.3` (Host satisfied)
  - Pre-installed dependencies in `pdoom-video/app/node_modules`:
    - `three` (`^0.186.0`)
    - `animejs` (`^4.5.0`)
    - `opentype.js` (`^2.0.0`)
    - `playwright-core` (`^1.63.0`)
    - `vite` (`^8.3.0`)
  - Google Chrome (Host satisfied)
  - Python with `uv` for `analysis/` (Host satisfied: `uv 0.13.0`)
- **Status**: Fully installed and ready for immediate rendering and development.

---

### Module 3: VoiceStudio (`./VoiceStudio`)
- **Repository**: `debpalash/VoiceStudio`
- **Location**: `f:\motion graphics\motion studio\VoiceStudio`
- **Primary Purpose**:
  - Full-featured AI audio production workstation.
  - Zero-shot voice cloning and custom voice design across 646 languages.
  - Multilingual TTS engines (OmniVoice, Kokoro, ChatterBox, CosyVoice).
  - High-precision speech-to-text / subtitle generation via Whisper.cpp.
  - Sound effects (SFX) generation via `moss_sfx`.
  - Voice dubbing and translation with stem separation.
- **Entry Points**:
  - FastAPI Backend: `VoiceStudio/backend/main.py`
  - MCP Server: `VoiceStudio/backend/mcp_server.py`
  - CLI: `VoiceStudio/cli/`
  - Docker Image: `ghcr.io/debpalash/voicestudio:stable` (or `palashdeb/omnivoice-studio:stable`)
- **Interface Protocol**:
  - REST API on `http://127.0.0.1:3900`.
  - OpenAI-compatible audio API on `http://127.0.0.1:3900/v1`:
    - `POST /v1/audio/speech`
    - `POST /v1/audio/transcriptions`
    - `GET /v1/audio/voices`
  - JSON payload requests and raw audio byte stream responses (MP3, WAV, Opus, FLAC).
- **Dependencies**:
  - Python `3.13.9` (Host satisfied)
  - NVIDIA GeForce RTX 3050 (4GB VRAM, CUDA 13.3 available)
  - PyTorch & torchaudio
- **Status**: Ready. Can be run locally via uvicorn in an isolated Python environment, or via container, or using the built-in `npx hyperframes tts` utility for fast standalone voiceover generation.

---

### Module 4: raea (`./raea`)
- **Repository**: `shinyobjectz/raea`
- **Location**: `f:\motion graphics\motion studio\raea`
- **Primary Purpose**:
  - Next-generation native renderer combining React/TSX syntax with Bevy 0.20 game engine and WGPU.
  - Zero-browser overhead: uses JavaScriptCore runtime embedded directly in Rust.
  - Integrates 3D glTF models, Gaussian splats, Bevy ECS, and Vello GPU vector painting.
  - Automated video quality inspection: `raea check` detects clipped text, low contrast, unsafe zones, and audio loudness violations.
- **Entry Points**:
  - CLI binary: `raea` (installed to `~/.raea/bin/raea.exe`)
  - Commands: `raea render <file.tsx> -o <out.mp4>`, `raea check <video.mp4>`, `raea play <file.tsx>`
- **Interface Protocol**:
  - CLI commands and React/TSX composition files.
- **Dependencies**:
  - DirectX 12 / Vulkan GPU driver (Host satisfied)
  - MSVC C++ Redistributable (Host satisfied)
  - Binary installable via `irm https://raea.io/install.ps1 | iex`
- **Status**: Canary / Research module. Keep repository clean; activate prebuilt binary when Bevy-specific features or hardware-accelerated TSX rendering is desired.

---

## 3. COMPATIBILITY & OVERLAP ASSESSMENT

| Feature | HyperFrames | pdoom-video | VoiceStudio | raea | Recommended Studio Tool |
|---|---|---|---|---|---|
| **3D Scenes / Shaders** | Canvas Hosted | Native Three.js + GLSL | None | Native Bevy / WGPU | **pdoom-video** |
| **Typography / Text Wipes** | GSAP / CSS | opentype.js / Anime.js | None | Vello / React | **pdoom-video** & **HyperFrames** |
| **UI / Slides / Vector** | Native HTML/SVG | Canvas2D | None | Taffy / React | **HyperFrames** |
| **Voiceover & Speech** | Local Kokoro-82M | None | Multi-engine / Clone | Foley / Synth | **VoiceStudio** (Pro) / **HyperFrames TTS** (Fast) |
| **Audio Alignment** | Beats / Hits JSON | Whisper CTC Forced Align | Whisper.cpp STT | Audio mixer | **pdoom-video/analysis** & **HyperFrames** |
| **Final Video Render** | Headless Chrome + FFmpeg | Headless Chrome + FFmpeg | Media Tools / FFmpeg | WGPU Hardware Encoder | **FFmpeg Pipeline** |
