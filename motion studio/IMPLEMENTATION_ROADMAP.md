# OpenGen Motion Graphics Studio: Implementation Roadmap & Execution Plan

This document outlines the step-by-step engineering roadmap for building the **OpenGen Motion Graphics Studio**, divided into nine distinct, testable development phases.

---

## Roadmap Overview

```mermaid
gantt
    title OpenGen Motion Graphics Studio Implementation Roadmap
    dateFormat  YYYY-MM-DD
    section Core Infrastructure
    Phase 1: Project & IR Schemas           :p1, 2026-12-01, 7d
    Phase 2: Animation Engines (2D & 3D)    :p2, after p1, 14d
    section Pipeline & Audio
    Phase 3: Headless Rendering Pipeline    :p3, after p2, 10d
    Phase 4: Audio, Voice & Sync            :p4, after p3, 10d
    section Templates & AI
    Phase 5: Template & Preset System       :p5, after p4, 8d
    Phase 6: AI Storyboard & Planning       :p6, after p5, 12d
    Phase 7: Reference Video Analysis       :p7, after p6, 10d
    section Protocols & Production
    Phase 8: MCP, REST API, CLI & SDK       :p8, after p7, 10d
    Phase 9: Performance Optimization       :p9, after p8, 12d
```

---

## Phase 1: Core Scene & Project Representation (IR)

### 1. Objectives & Scope
Define the engine-agnostic intermediate representation (IR) JSON schema, TypeScript interfaces, Python Pydantic models, and strict validation logic.

### 2. Files & Modules to Create
* `packages/core/src/schema/project.schema.json`
* `packages/core/src/types/ir.ts` (TypeScript interfaces)
* `python/opengen/core/models/ir.py` (Python Pydantic v2 models)
* `packages/core/src/validation/validator.ts` (Ajv-based JSON validator)
* `packages/core/src/builder/ProjectBuilder.ts` (Fluent builder API for programmatic construction)

### 3. Packages & Dependencies
* `ajv` (`^8.17.1`), `ajv-formats`
* `pydantic` (`^2.10.0`)
* `zod` (`^3.24.0`)

### 4. APIs to Implement
* `validateProject(projectJson: unknown): ValidationResult`
* `ProjectBuilder.create(settings).addScene(scene).build(): OpenGenProject`
* `SceneBuilder.create(id, duration).addLayer(layer).build(): Scene`

### 5. Verification & Tests
* Unit tests validating compliant projects across aspect ratios (16:9, 9:16, 1:1, 4:5).
* Negative unit tests catching invalid durations, overlapping time bounds, unknown easings, and malformed color hex codes.

### 6. Acceptance Criteria
* Zero schema validation drift between TypeScript and Python models.
* Validation execution completes in under 5 milliseconds for a 50-scene project.

---

## Phase 2: Animation Engines (2D & 3D Adapters)

### 1. Objectives & Scope
Implement the animation compilers that translate OpenGen IR into runnable 2D HTML/GSAP and 3D Three.js/Anime.js render graphs.

### 2. Files & Modules to Create
* `packages/engine-hyperframes/src/compiler/HtmlCompiler.ts`
* `packages/engine-hyperframes/src/compiler/GsapTweenMapper.ts`
* `packages/engine-pdoom/src/compiler/ThreeSceneFactory.ts`
* `packages/engine-pdoom/src/shaders/PostProcessingPass.ts`
* `packages/engine-common/src/easings/EasingResolver.ts`

### 3. Packages & Dependencies
* `gsap` (`^3.12.5`)
* `three` (`^0.186.0`), `@types/three`
* `animejs` (`^4.5.0`)
* `opentype.js` (`^2.0.0`)

### 4. APIs to Implement
* `HtmlCompiler.compile(scene: Scene): { html: string, timelineJs: string }`
* `ThreeSceneFactory.createScene(scene: Scene): SceneBase`
* `GsapTweenMapper.map(animation: Animation): string`

### 5. Verification & Tests
* Snapshot testing comparing generated HTML strings against golden references.
* WebGL headless context initialization check under headless Linux.

### 6. Acceptance Criteria
* Generated 2D timelines pause deterministically at `t = 0`.
* Seeking `window.__timelines[sceneId].seek(t)` displays correct frame transforms without jitter.

---

## Phase 3: Headless Timeline & Video Rendering

### 1. Objectives & Scope
Build the deterministic frame capture loop using headless Chrome via Playwright/CDP and stream raw pixel buffers directly into FFmpeg stdin.

### 2. Files & Modules to Create
* `packages/renderer/src/browser/BrowserPool.ts` (Playwright instance pooling)
* `packages/renderer/src/capture/FrameGrabber.ts` (CDP screenshot buffer capture)
* `packages/renderer/src/ffmpeg/FfmpegPipeWriter.ts` (stdin rawvideo piping)
* `packages/renderer/src/render/RenderJobRunner.ts` (Job management, progress reporting)
* `packages/renderer/src/cache/FrameCache.ts` (Scene-level hash caching)

### 3. Packages & Dependencies
* `playwright-core` (`^1.63.0`)
* `execa` (`^9.5.0`)
* `ffprobe` / `ffmpeg-static`

### 4. APIs to Implement
* `RenderJobRunner.renderScene(scene: Scene, options: RenderOptions): Promise<string>`
* `RenderJobRunner.renderProject(project: OpenGenProject): Promise<string>`
* `BrowserPool.acquire(): Promise<Page>`

### 5. Verification & Tests
* Render a 300-frame 1080x1920 test scene to MP4 and verify zero dropped frames.
* Measure RAM consumption: verify Chrome memory stays bounded under 1.5 GB.

### 6. Acceptance Criteria
* Hardware acceleration (NVENC / QuickSync) automatically engages when available.
* Progress event (`progress: number`, `fps: number`, `eta: number`) fires every second.

---

## Phase 4: Audio Engine & Multi-Track Synchronization

### 1. Objectives & Scope
Implement TTS generation (VoiceStudio / Kokoro), audio waveform analysis, beat detection, volume ducking, and EBU R128 loudness normalization.

### 2. Files & Modules to Create
* `python/opengen/audio/tts_client.py` (VoiceStudio & Kokoro HTTP client)
* `python/opengen/audio/beat_analyzer.py` (Librosa tempo & beat grid extraction)
* `python/opengen/audio/aligner.py` (Faster-Whisper word-level timestamp extraction)
* `packages/renderer/src/audio/AudioMuxer.ts` (FFmpeg complex audio filtergraphs)

### 3. Packages & Dependencies
* `faster-whisper` (`^1.1.0`)
* `librosa` (`^0.10.2`)
* `soundfile` (`^0.13.0`)
* `requests` / `httpx`

### 4. APIs to Implement
* `VoiceClient.synthesize(text: str, voice: str) -> str`
* `BeatAnalyzer.get_beats(audio_path: str) -> AudioTelemetry`
* `Aligner.get_word_timestamps(audio_path: str) -> List[WordMarker]`
* `AudioMuxer.mux(videoPath: string, tracks: AudioTrack[]): Promise<string>`

### 5. Verification & Tests
* Audio loudness test: verify output MP4 measures between -13.5 and -14.5 LUFS.
* Beat alignment test: verify cut timestamps coincide with detected beat markers ($\pm 1$ frame).

### 6. Acceptance Criteria
* Background music ducks cleanly by 14dB whenever voiceover is active.
* Subtitle word timestamps align within 33ms (1 frame at 30fps) of speech audio.

---

## Phase 5: Template & Preset System

### 1. Objectives & Scope
Create 10 production-ready reusable motion graphics templates covering commercials, explainers, reels, and statistics, with dynamic placeholder replacement.

### 2. Files & Modules to Create
* `templates/product-ad/template.json`
* `templates/tech-explainer/template.json`
* `templates/educational/template.json`
* `templates/instagram-reel/template.json`
* `templates/corporate-promo/template.json`
* `templates/animated-stats/template.json`
* `templates/news-ticker/template.json`
* `templates/logo-reveal/template.json`
* `templates/kinetic-type/template.json`
* `templates/app-showcase/template.json`
* `packages/core/src/templates/TemplateResolver.ts`

### 3. APIs to Implement
* `TemplateResolver.load(templateId: string): Template`
* `TemplateResolver.hydrate(template: Template, variables: Record<string, any>): OpenGenProject`

### 4. Verification & Tests
* Render every template with variable overrides across all 4 aspect ratios.

### 5. Acceptance Criteria
* Zero text clipping or visual collisions across aspect ratio mutations.

---

## Phase 6: AI Storyboard & Planning Engine

### 1. Objectives & Scope
Integrate multi-provider LLMs (Gemini, OpenAI, Anthropic, Ollama) via a unified Provider Manager to turn natural language briefs into structured OpenGen IR JSON.

### 2. Files & Modules to Create
* `python/opengen/ai/providers/base.py` (Abstract provider interface)
* `python/opengen/ai/providers/gemini_provider.py` (`google-genai` SDK)
* `python/opengen/ai/providers/openai_provider.py` (`openai` SDK)
* `python/opengen/ai/providers/anthropic_provider.py` (`anthropic` SDK)
* `python/opengen/ai/providers/ollama_provider.py` (Local offline LLM)
* `python/opengen/ai/director.py` (Script, Storyboard, and Scene Planner)

### 3. APIs to Implement
* `Director.create_storyboard(prompt: str, config: StoryboardConfig) -> OpenGenProject`
* `Director.refine_scene(scene: Scene, feedback: str) -> Scene`

### 4. Verification & Tests
* Prompt fuzzing: test 50 diverse creative briefs and verify 100% JSON parse compliance.
* Test offline fallback to Ollama when cloud API keys are absent.

### 5. Acceptance Criteria
* Valid OpenGen IR returned in a single turn without hallucinated property names.

---

## Phase 7: Reference Video Analysis Engine

### 1. Objectives & Scope
Analyze user-uploaded reference videos: detect cut boundaries, camera motions, color palettes, typography, and audio tracks to generate an editable project inspired by the reference.

### 2. Files & Modules to Create
* `python/opengen/analysis/scene_detector.py` (PySceneDetect)
* `python/opengen/analysis/palette_extractor.py` (K-Means color clustering)
* `python/opengen/analysis/ocr_extractor.py` (Text detection on keyframes)
* `python/opengen/analysis/multimodal_vision.py` (Gemini 2.0 Flash / Vision breakdown)
* `python/opengen/analysis/reverser.py` (Assemble reverse project)

### 3. Packages & Dependencies
* `scenedetect[opencv]`
* `scikit-learn` (Color clustering)
* `pillow`, `numpy`

### 4. APIs to Implement
* `VideoReverser.analyze(video_path: str) -> VideoDecomposition`
* `VideoReverser.generate_twin_project(analysis: VideoDecomposition) -> OpenGenProject`

### 5. Verification & Tests
* Run analysis on sample 15s MP4; compare detected cuts with manual ground truth.

### 6. Acceptance Criteria
* Scene detection achieves >95% precision on hard cuts and wipes.

---

## Phase 8: MCP, REST API, CLI & SDK

### 1. Objectives & Scope
Expose the complete studio capabilities to AI coding agents via Model Context Protocol (MCP), a Python SDK, a TypeScript SDK, a FastAPI REST server, and a CLI.

### 2. Files & Modules to Create
* `python/opengen/mcp/server.py` (FastMCP / MCP server implementation)
* `python/opengen/api/routes.py` (FastAPI REST endpoints)
* `python/opengen/sdk/client.py` (Python SDK)
* `packages/cli/src/index.ts` (Command-line tool `opengen motion ...`)

### 3. APIs to Implement
* MCP Tools: `create_motion_graphics`, `analyze_reference_video`, `render_video`, `get_render_status`
* REST Endpoints: `POST /api/v1/projects`, `POST /api/v1/render`, `GET /api/v1/jobs/{id}`

### 4. Verification & Tests
* Automated MCP protocol compliance tests via standard MCP client harness.
* End-to-end CLI render invocation tests.

### 5. Acceptance Criteria
* AI coding agents can plan, modify, and render a complete video using only MCP tool calls.

---

## Phase 9: Performance Optimization & Production Readiness

### 1. Objectives & Scope
Implement scene hash caching, parallel scene rendering, NVENC hardware encoder optimization, and Docker container security hardening.

### 2. Key Tasks
* Implement SHA-256 hash caching on scene JSON: avoid re-rendering untouched scenes.
* Benchmark concurrent render worker limits across CPU/GPU cores.
* Add rate-limiting, sandboxing, and temporary file lifecycle cleanup.
* Build multi-arch Docker image with NVIDIA runtime support.

### 3. Acceptance Criteria
* Re-rendering a project with 1 modified scene finishes in under 3 seconds (re-muxing cached scenes).
* Zero orphan FFmpeg or Chrome processes left on server crashes.
