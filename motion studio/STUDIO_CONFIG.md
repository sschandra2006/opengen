# STUDIO CONFIGURATION SPECIFICATION (`STUDIO_CONFIG.md`)

This document defines standard configurations, rendering profiles, aspect ratios, audio standards, directory conventions, and environment variables across the AI Animated Video Production Studio.

---

## 1. VIDEO STANDARDS & FORMAT PROFILES

| Profile Name | Target Platform | Resolution | Aspect Ratio | Default FPS | Bitrate Target | CRF Preset |
|---|---|---|---|---|---|---|
| **Reel-Vertical** *(Default)* | Instagram Reels, TikTok, YouTube Shorts | **1080 × 1920** | **9:16** | **30 FPS** (60 FPS optional) | 8-12 Mbps | CRF 18 (libx264) |
| **Cinema-Horizontal** | YouTube, Website Headers, Television Ads | **1920 × 1080** | **16:9** | **30 / 60 FPS** | 12-16 Mbps | CRF 17 (libx264) |
| **Square-Feed** | Instagram Feed, LinkedIn, Twitter/X | **1080 × 1080** | **1:1** | **30 FPS** | 6-10 Mbps | CRF 18 (libx264) |
| **Ultra-4K-Master** | Archival / Master Showcase | **3840 × 2160** | **16:9** | **60 FPS** | 35-50 Mbps | CRF 15 (libx264) |

### Video Encoder Parameters (FFmpeg)
- **Video Codec**: `libx264` (universal compatibility) or `h264_nvenc` (fast GPU encoding via NVIDIA RTX 3050)
- **Pixel Format**: `yuv420p` (essential for web & mobile playback compatibility)
- **Color Space**: `bt709`
- **Tuning**: `--tune animation` (optimizes line sharpness and flat colors for motion graphics)
- **Keyframe Interval**: Every 60 frames (GOP = 2s @ 30 FPS)

---

## 2. AUDIO STANDARDS & LOUDNESS COMPLIANCE

Social media and video streaming platforms automatically down-rank or aggressively clamp audio that does not adhere to broadcast loudness standards.

| Metric | Target Standard | Description |
|---|---|---|
| **Integrated Loudness** | **-14.0 LUFS** (±0.5 LUFS) | Standard for Instagram Reels, YouTube, Spotify, and TikTok |
| **True Peak (Max)** | **-1.5 dBTP** | Prevents inter-sample clipping during AAC conversion on mobile |
| **Loudness Range (LRA)** | **4.0 - 7.0 LU** | Ensures dialogue remains audible over background music on phone speakers |
| **Sample Rate** | **48,000 Hz (48 kHz)** | Video broadcast standard (avoids resampling jitter) |
| **Bit Depth** | **16-bit** PCM (internal mix at 32-bit float) | Prevents quantization distortion |
| **Channels** | **2 (Stereo)** | Clean channel separation with central dialogue |

---

## 3. STUDIO DIRECTORY STRUCTURE

The workspace follows a strict folder structure to maintain project cleanliness and prevent source pollution:

```
f:\motion graphics\motion studio\
|-- AGENTS.md                   # Core instruction manual for all AI agents
|-- MODULE_REGISTRY.md          # Technical registry of all cloned modules
|-- STUDIO_CONFIG.md            # Video/audio/directory configuration specification
|-- WORKFLOWS.md                # Reusable production workflows
|-- INTEGRATION_MAP.md          # Inter-module communication and dataflow map
|-- .env                        # Local environment secrets and paths
|-- .env.example                # Template for environment configuration
|
|-- hyperframes/                # Cloned HyperFrames engine (HTML/CSS/GSAP)
|-- pdoom-video/                # Cloned pdoom-video engine (Three.js/Anime.js)
|-- VoiceStudio/                # Cloned VoiceStudio engine (FastAPI/TTS/ASR)
|-- raea/                       # Cloned raea engine (Rust/Bevy)
|
|-- studio/                     # Unified Studio Orchestrator & CLI tools
|   |-- orchestrator.ts         # Central pipeline coordinator
|   |-- audio_pipeline.py       # Audio generation & alignment bridge
|   `-- render_bridge.ts        # Dispatcher to target renderer
|
|-- templates/                  # Reusable video composition templates
|   |-- 15s_reel_typography/    # Fast kinetic typography template
|   |-- 30s_product_showcase/   # 3D product showcase template
|   `-- 60s_educational/        # Educational explainer template
|
|-- assets/                     # Shared studio assets
|   |-- fonts/                  # TTF, OTF, and WOFF2 fonts
|   |-- audio/                  # Stock SFX, ambient beds, stems
|   |-- models/                 # 3D glTF / GLB assets
|   `-- textures/               # HDRI environments, materials, noise maps
|
`-- out/                        # Default output directory for all rendered artifacts
    |-- wip/                    # Intermediate test frames and contact sheets
    `-- final/                  # Final exported MP4 and WebM videos
```

---

## 4. ENVIRONMENT VARIABLES (`.env`)

```ini
# ==========================================
# AI ANIMATED VIDEO PRODUCTION STUDIO (.env)
# ==========================================

# Studio Base Paths
STUDIO_ROOT="F:\\motion graphics\\motion studio"
STUDIO_OUT_DIR="F:\\motion graphics\\motion studio\\out"
STUDIO_ASSET_DIR="F:\\motion graphics\\motion studio\\assets"

# System Binaries
FFMPEG_PATH="ffmpeg"
CHROME_PATH="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
BUN_PATH="bun"
NODE_PATH="node"

# GPU Configuration
CUDA_VISIBLE_DEVICES="0"
GPU_ACCELERATION="true"

# VoiceStudio Backend
VOICESTUDIO_HOST="127.0.0.1"
VOICESTUDIO_PORT="3900"
VOICESTUDIO_API_URL="http://127.0.0.1:3900"
OMNIVOICE_API_KEY=""

# Optional Cloud AI Keys (Only if using external services)
# OPENAI_API_KEY=""
# ELEVENLABS_API_KEY=""
# HEYGEN_API_KEY=""
```

---

## 5. RENDER ENGINE SELECTION RULES

Future agents must choose the appropriate engine based on the creative requirements of the prompt:

1. **Rule 1: Kinetic Typography / Beat-Matched Lyrics / Shader FX**
   - **Engine**: `pdoom-video`
   - **Why**: Features sub-frame deterministic time synchronization, `opentype.js` vector outlines, and real-time bloom/film grain post-processing shaders.

2. **Rule 2: Complex 3D Objects / Camera Movements / Particle Clouds**
   - **Engine**: `pdoom-video`
   - **Why**: Native Three.js (v0.186) support with GLSL shaders and headless Chrome multi-sampled offline rendering.

3. **Rule 3: Clean UI Mockups / Explainer Cards / Slideshows / Lower-Thirds**
   - **Engine**: `hyperframes`
   - **Why**: Declarative HTML/CSS layout, GSAP timeline scrubbing, zero bundler overhead, instant local preview (`preview` on port 3002).

4. **Rule 4: Narration / Voice Cloning / Dialogue**
   - **Engine**: `VoiceStudio` (or `hyperframes tts` for fast offline generation).
