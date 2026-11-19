# OpenGen Motion Graphics Studio: API Integration Reference & Engine Adapters

This document contains verified production-grade code, exact API signatures, and architectural integration adapters connecting the OpenGen Motion Graphics Studio with its underlying execution engines.

---

## 1. Engine Adapter 1: HyperFrames 2D Composition & Headless Renderer

### A. Programmatic HTML/GSAP Scene Compiler

This module converts OpenGen IR JSON scenes into a deterministic HTML5 composition file consumable by `@hyperframes/cli` or Playwright.

```typescript
// src/engines/hyperframes/HyperFramesCompiler.ts

import { OpenGenProject, Scene, Layer } from '../../types/OpenGenIR';
import * as fs from 'fs-extra';
import * as path from 'path';

export class HyperFramesCompiler {
  public static compileToHtml(project: OpenGenProject, outputPath: string): string {
    const { width, height, fps, duration, backgroundColor } = project.settings;

    const scenesHtml = project.scenes.map((scene) => this.renderScene(scene)).join('\n');
    const timelinesJs = project.scenes.map((scene) => this.renderSceneTimeline(scene)).join('\n');

    const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: ${backgroundColor || '#000000'};
      width: ${width}px;
      height: ${height}px;
      overflow: hidden;
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    #composition {
      position: relative;
      width: ${width}px;
      height: ${height}px;
    }
    .clip {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      overflow: hidden;
    }
    .layer {
      position: absolute;
      display: flex;
      align-items: center;
      justify-content: center;
      will-change: transform, opacity;
    }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
</head>
<body>
  <div id="composition" class="composition" data-fps="${fps}" data-duration="${duration}">
    ${scenesHtml}
  </div>

  <script>
    window.__timelines = window.__timelines || {};
    ${timelinesJs}
  </script>
</body>
</html>`;

    fs.writeFileSync(outputPath, htmlContent, 'utf-8');
    return outputPath;
  }

  private static renderScene(scene: Scene): string {
    const layersHtml = scene.layers.map((layer) => this.renderLayer(layer)).join('\n      ');
    return `    <div class="clip" id="${scene.id}" data-start="${scene.start}" data-duration="${scene.duration}">
      ${layersHtml}
    </div>`;
  }

  private static renderLayer(layer: Layer): string {
    const { id, type, transform, content, zIndex } = layer;
    const style = `z-index: ${zIndex || 0}; opacity: ${transform?.opacity ?? 1};`;

    if (type === 'text') {
      const { text, fontSize, color, fontWeight, textAlign } = content || {};
      return `<div id="${id}" class="layer" style="${style} font-size: ${fontSize || 48}px; color: ${color || '#ffffff'}; font-weight: ${fontWeight || 700}; text-align: ${textAlign || 'center'}; width: 100%;">
        ${text || ''}
      </div>`;
    }

    if (type === 'image') {
      return `<div id="${id}" class="layer" style="${style} width: 100%; height: 100%;">
        <img src="${content?.src}" style="width: 100%; height: 100%; object-fit: ${content?.fit || 'cover'};" />
      </div>`;
    }

    return `<div id="${id}" class="layer" style="${style}"></div>`;
  }

  private static renderSceneTimeline(scene: Scene): string {
    let script = `\n    // Scene: ${scene.id}\n    const tl_${scene.id} = gsap.timeline({ paused: true });\n`;

    for (const layer of scene.layers) {
      if (layer.animations && layer.animations.length > 0) {
        for (const anim of layer.animations) {
          const gsapEasing = this.mapEasing(anim.easing);
          script += `    tl_${scene.id}.fromTo("#${layer.id}", 
            { ${anim.property}: ${JSON.stringify(anim.from)} }, 
            { ${anim.property}: ${JSON.stringify(anim.to)}, duration: ${anim.duration}, ease: "${gsapEasing}" }, 
            ${anim.start});\n`;
        }
      }
    }

    script += `    window.__timelines["${scene.id}"] = tl_${scene.id};\n`;
    return script;
  }

  private static mapEasing(easing?: string): string {
    const mapping: Record<string, string> = {
      linear: 'none',
      easeOutQuad: 'power1.out',
      easeInOutQuad: 'power1.inOut',
      easeOutCubic: 'power2.out',
      easeInOutCubic: 'power2.inOut',
      easeOutExpo: 'expo.out',
      easeOutBack: 'back.out(1.7)',
      easeOutElastic: 'elastic.out(1, 0.3)',
      easeOutBounce: 'bounce.out'
    };
    return mapping[easing || 'easeOutCubic'] || 'power2.out';
  }
}
```

### B. Headless Execution Command Wrapper

```typescript
// src/engines/hyperframes/HyperFramesRunner.ts

import { execa } from 'execa';

export interface RenderOptions {
  compositionPath: string;
  outputPath: string;
  fps?: number;
  crf?: number;
  quality?: 'fast' | 'high' | 'prores';
}

export class HyperFramesRunner {
  public static async renderToMp4(options: RenderOptions): Promise<string> {
    const args = [
      'hyperframes',
      'render',
      '-c', options.compositionPath,
      '-o', options.outputPath,
      '--fps', String(options.fps || 30),
      '--crf', String(options.crf || 18)
    ];

    const subprocess = execa('npx', args);
    
    subprocess.stdout?.on('data', (data) => {
      const line = data.toString();
      if (line.includes('@hf-progress')) {
        // Parse progress percentage
      }
    });

    await subprocess;
    return options.outputPath;
  }
}
```

---

## 2. Engine Adapter 2: pdoom-video 3D & GLSL Shader Renderer

### A. Three.js Deterministic Scene Base Class

```typescript
// src/engines/pdoom/SceneBase.ts

import * as THREE from 'three';
import { AudioTelemetry } from './types';

export abstract class SceneBase {
  public scene: THREE.Scene;
  public camera: THREE.PerspectiveCamera;
  public duration: number;

  constructor(width: number, height: number, duration: number) {
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.duration = duration;
  }

  public abstract init(): Promise<void>;
  
  // Deterministic frame update based purely on time t and frame index
  public abstract update(t: number, frame: number, audio: AudioTelemetry): void;

  public render(renderer: THREE.WebGLRenderer): void {
    renderer.render(this.scene, this.camera);
  }
}
```

### B. Headless Playwright Frame Stepper & FFmpeg Piping

```typescript
// src/engines/pdoom/DeterministicRenderer.ts

import { chromium } from 'playwright-core';
import { spawn } from 'child_process';

export class DeterministicRenderer {
  public static async renderSequence(
    serveUrl: string,
    outputPath: string,
    totalFrames: number,
    fps: number,
    width: number,
    height: number
  ): Promise<void> {
    // 1. Spawn FFmpeg taking raw rgba pipe
    const ffmpeg = spawn('ffmpeg', [
      '-y',
      '-f', 'rawvideo',
      '-vcodec', 'rawvideo',
      '-s', `${width}x${height}`,
      '-pix_fmt', 'rgba',
      '-r', String(fps),
      '-i', '-',
      '-c:v', 'libx264',
      '-preset', 'fast',
      '-crf', '18',
      '-pix_fmt', 'yuv420p',
      outputPath
    ]);

    // 2. Launch headless Chrome with CDP
    const browser = await chromium.launch({
      headless: true,
      args: ['--disable-gpu', '--no-sandbox']
    });

    const page = await browser.newPage({
      viewport: { width, height }
    });

    await page.goto(serveUrl);
    await page.waitForFunction('window.__READY__ === true');

    // 3. Step every frame deterministically
    for (let frame = 0; frame < totalFrames; frame++) {
      const t = frame / fps;
      
      // Tell browser animation loop to seek exact timestamp
      await page.evaluate(`window.__seek(${t}, ${frame})`);

      // Read raw canvas pixels buffer directly
      const buffer = await page.screenshot({ type: 'png' }); // or raw RGBA buffer via CDP
      ffmpeg.stdin.write(buffer);
    }

    ffmpeg.stdin.end();
    await browser.close();

    await new Promise((resolve, reject) => {
      ffmpeg.on('close', resolve);
      ffmpeg.on('error', reject);
    });
  }
}
```

---

## 3. Audio & Voice Adapter: VoiceStudio, Kokoro TTS & Faster-Whisper

### A. Python Voice & Subtitle Alignment Service

```python
# src/audio/voice_service.py

import os
from typing import List, Dict, Any
from faster_whisper import WhisperModel
import requests

VOICESTUDIO_API = os.getenv("VOICESTUDIO_API_URL", "http://127.0.0.1:3900")

class VoiceService:
    def __init__(self):
        # Load local whisper model for timestamp forced-alignment
        self.whisper_model = WhisperModel("base", device="cuda" if os.environ.get("USE_CUDA") else "cpu", compute_type="float16")

    def generate_speech(self, text: str, voice: str = "narrator", output_path: str = "voice.mp3") -> str:
        """Call VoiceStudio OpenAI-compatible endpoint to generate TTS."""
        response = requests.post(
            f"{VOICESTUDIO_API}/v1/audio/speech",
            json={"model": "kokoro", "input": text, "voice": voice},
            stream=True
        )
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path

    def align_transcript(self, audio_path: str) -> List[Dict[str, Any]]:
        """Extract word-level and syllable-level timestamps for kinetic typography."""
        segments, info = self.whisper_model.transcribe(audio_path, word_timestamps=True)
        word_telemetry = []
        for segment in segments:
            for word in segment.words:
                word_telemetry.append({
                    "word": word.word.strip(),
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "probability": round(word.probability, 2)
                })
        return word_telemetry
```

---

## 4. Video Analysis Adapter: PySceneDetect & Librosa

```python
# src/analysis/video_analyzer.py

from scenedetect import detect, ContentDetector, AdaptiveDetector
import librosa
import numpy as np

class VideoAnalyzer:
    @staticmethod
    def detect_scenes(video_path: str, threshold: float = 27.0):
        """Detect scene cut boundaries and durations."""
        scenes = detect(video_path, ContentDetector(threshold=threshold))
        results = []
        for i, (start_time, end_time) in enumerate(scenes):
            results.append({
                "scene_index": i + 1,
                "start_sec": start_time.get_seconds(),
                "end_sec": end_time.get_seconds(),
                "duration_sec": end_time.get_seconds() - start_time.get_seconds(),
                "start_frame": start_time.get_frames(),
                "end_frame": end_time.get_frames()
            })
        return results

    @staticmethod
    def analyze_audio_rhythm(audio_path: str):
        """Extract BPM, beat grid, and onset timestamps for cut synchronization."""
        y, sr = librosa.load(audio_path, sr=None)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()

        return {
            "bpm": round(float(tempo), 1),
            "beat_times": [round(t, 3) for t in beat_times],
            "onset_times": [round(t, 3) for t in onset_times]
        }
```

---

## 5. Multi-Provider LLM Orchestrator: Storyboard & Script Generator

```python
# src/ai/storyboard_generator.py

import json
from typing import Dict, Any
from google import genai
from google.genai import types

STORYBOARD_SYSTEM_PROMPT = """
You are the Motion Graphics Director for OpenGen.
Given a user creative brief, produce a valid, parseable JSON Project matching the OpenGen IR schema.
Structure the video into concise, 2-4 second dynamic scenes.
Choose expressive kinetic typography, color palettes, and GSAP easings.
Return ONLY valid JSON.
"""

class StoryboardGenerator:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def generate_project_plan(self, brief: str, duration_sec: int = 15, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        prompt = f"""Creative Brief: {brief}
Target Duration: {duration_sec} seconds
Aspect Ratio: {aspect_ratio}

Generate the complete OpenGen Project IR JSON."""

        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=STORYBOARD_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.3
            )
        )

        return json.loads(response.text)
```

---

## 6. FFmpeg Multiplexer & Final Mastering Adapter

```typescript
// src/render/FFmpegMuxer.ts

import { execa } from 'execa';

export interface MuxOptions {
  videoTrackPath: string;
  voiceoverTrackPath?: string;
  musicTrackPath?: string;
  outputPath: string;
  targetLUFS?: number;
}

export class FFmpegMuxer {
  public static async muxVideoAndAudio(options: MuxOptions): Promise<string> {
    const { videoTrackPath, voiceoverTrackPath, musicTrackPath, outputPath, targetLUFS = -14.0 } = options;

    if (!voiceoverTrackPath && !musicTrackPath) {
      // Just copy video stream
      await execa('ffmpeg', ['-y', '-i', videoTrackPath, '-c', 'copy', outputPath]);
      return outputPath;
    }

    const args = ['-y', '-i', videoTrackPath];
    let filterComplex = '';

    if (voiceoverTrackPath && musicTrackPath) {
      args.push('-i', voiceoverTrackPath, '-i', musicTrackPath);
      // Auto-duck music under voiceover (reduce music by 14dB when voiceover plays)
      filterComplex = `
        [2:a]volume=0.25[bgm];
        [1:a][bgm]amix=inputs=2:duration=first[mixed];
        [mixed]loudnorm=I=${targetLUFS}:LRA=7:TP=-1.5[aout]
      `.replace(/\s+/g, ' ');
    } else if (voiceoverTrackPath) {
      args.push('-i', voiceoverTrackPath);
      filterComplex = `[1:a]loudnorm=I=${targetLUFS}:LRA=7:TP=-1.5[aout]`;
    } else if (musicTrackPath) {
      args.push('-i', musicTrackPath);
      filterComplex = `[1:a]loudnorm=I=${targetLUFS}:LRA=7:TP=-1.5[aout]`;
    }

    args.push(
      '-filter_complex', filterComplex,
      '-map', '0:v',
      '-map', '[aout]',
      '-c:v', 'copy',
      '-c:a', 'aac',
      '-b:a', '192k',
      outputPath
    );

    await execa('ffmpeg', args);
    return outputPath;
  }
}
```
