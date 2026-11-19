import { OpenGenProject, ProjectValidator } from '@opengen/core';
import { HtmlCompiler } from '@opengen/engine-hyperframes';
import { ThreeSceneFactory } from '@opengen/engine-pdoom';
import { DeterministicRenderer } from '../render/DeterministicRenderer';
import { AudioMuxer } from '../audio/AudioMuxer';
import { FrameCache } from '../cache/FrameCache';
import * as path from 'node:path';
import * as fs from 'node:fs';

export interface RenderJobOptions {
  outputPath?: string;
  fps?: number;
  crf?: number;
  useCache?: boolean;
  onProgress?: (percent: number, message: string) => void;
}

export class RenderJobRunner {
  private cache: FrameCache;

  constructor() {
    this.cache = new FrameCache();
  }

  public async renderProject(project: OpenGenProject, options: RenderJobOptions = {}): Promise<string> {
    // 1. Validate Project IR
    const validation = ProjectValidator.validate(project);
    if (!validation.valid) {
      throw new Error(`Invalid OpenGen Project IR: ${JSON.stringify(validation.errors, null, 2)}`);
    }

    const fps = options.fps || project.settings.fps || 30;
    const finalOut = options.outputPath || path.resolve(process.cwd(), 'out', 'final', `${project.projectId}.mp4`);
    const tempDir = path.resolve(process.cwd(), 'out', 'wip', project.projectId);

    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }

    // Check if any scene requires 3D (pdoom-video)
    const has3D = project.scenes.some(s => s.preferredEngine === 'pdoom-video');

    const rawVideoPath = path.join(tempDir, 'raw_visuals.mp4');

    if (!has3D) {
      // 2D Engine: Compile to HTML5 + GSAP, then render deterministically via Headless Chrome
      options.onProgress?.(5, 'Compiling 2D HTML/GSAP composition...');
      const htmlPath = path.join(tempDir, 'index.html');
      HtmlCompiler.compileToHtml(project, htmlPath);

      options.onProgress?.(15, 'Rendering frames via Headless Chrome & NVENC hardware acceleration...');
      await DeterministicRenderer.renderHtmlToMp4({
        htmlPath,
        outputPath: rawVideoPath,
        width: project.settings.width,
        height: project.settings.height,
        fps,
        duration: project.settings.duration,
        onProgress: (pct, msg) => options.onProgress?.(15 + Math.floor(pct * 0.65), msg)
      });
    } else {
      // 3D Engine: pdoom-video Three.js + Anime.js + WebGL shaders
      options.onProgress?.(15, 'Rendering 3D sequence via pdoom-video engine...');
      const isLandscape = project.settings.aspectRatio === '16:9';
      await ThreeSceneFactory.renderPdoomScene({
        from: 0,
        to: project.settings.duration,
        fps,
        landscape: isLandscape,
        outputPath: rawVideoPath,
        onProgress: (pct, msg) => options.onProgress?.(15 + Math.floor(pct * 0.65), msg)
      });
    }

    // Identify voiceover and music audio tracks
    let voTrackPath: string | undefined;
    let bgmTrackPath: string | undefined;

    // Check globalAudio
    if (project.globalAudio) {
      for (const track of project.globalAudio) {
        if (track.type === 'voiceover' && fs.existsSync(track.src)) {
          voTrackPath = track.src;
        } else if (track.type === 'music' && fs.existsSync(track.src)) {
          bgmTrackPath = track.src;
        }
      }
    }

    // Check scene audioTracks if no global voiceover
    if (!voTrackPath) {
      for (const scene of project.scenes) {
        if (scene.audioTracks) {
          for (const track of scene.audioTracks) {
            if (track.type === 'voiceover' && fs.existsSync(track.src)) {
              voTrackPath = track.src;
              break;
            }
          }
        }
        if (voTrackPath) break;
      }
    }

    // Final Audio Mastering & Muxing (Auto-ducking + EBU R128)
    options.onProgress?.(85, 'Mastering audio with ducking & EBU R128 (-14 LUFS)...');
    await AudioMuxer.mux({
      videoTrackPath: rawVideoPath,
      voiceoverTrackPath: voTrackPath,
      musicTrackPath: bgmTrackPath,
      outputPath: finalOut,
      targetLUFS: project.settings.audio?.targetLUFS ?? -14.0,
      truePeak: project.settings.audio?.truePeak ?? -1.5
    });

    options.onProgress?.(100, `Video successfully rendered and mastered: ${finalOut}`);
    return finalOut;
  }
}
