import { chromium, type Browser, type Page } from 'playwright-core';
import { execSync } from 'node:child_process';
import * as path from 'node:path';
import * as fs from 'node:fs';

export interface DeterministicRenderOptions {
  htmlPath: string;
  outputPath: string;
  width: number;
  height: number;
  fps: number;
  duration: number;
  onProgress?: (percent: number, message: string) => void;
}

export class DeterministicRenderer {
  private static checkNvenc(): boolean {
    try {
      const encoders = execSync('ffmpeg -encoders', { encoding: 'utf-8' });
      return encoders.includes('h264_nvenc');
    } catch {
      return false;
    }
  }

  public static async renderHtmlToMp4(options: DeterministicRenderOptions): Promise<string> {
    const { htmlPath, outputPath, width, height, fps, duration, onProgress } = options;

    const outDir = path.dirname(outputPath);
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    const totalFrames = Math.ceil(duration * fps);
    const hasNvenc = this.checkNvenc();

    // 1. Configure FFmpeg taking image2pipe PNG from stdin
    const ffmpegArgs = [
      'ffmpeg',
      '-y',
      '-loglevel', 'error',
      '-f', 'image2pipe',
      '-vcodec', 'png',
      '-r', String(fps),
      '-i', 'pipe:0',
      '-an'
    ];

    if (hasNvenc) {
      ffmpegArgs.push(
        '-c:v', 'h264_nvenc',
        '-preset', 'p7',
        '-cq', '18',
        '-pix_fmt', 'yuv420p'
      );
    } else {
      ffmpegArgs.push(
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-pix_fmt', 'yuv420p'
      );
    }

    ffmpegArgs.push(outputPath);

    // Spawn native Bun process with high-speed pipe
    const ff = Bun.spawn(ffmpegArgs, {
      stdin: 'pipe',
      stdout: 'ignore',
      stderr: 'inherit'
    });

    // 2. Launch Google Chrome headlessly with GPU acceleration
    const browser = await chromium.launch({
      channel: 'chrome',
      headless: true,
      args: [
        '--use-angle=d3d11',
        '--enable-gpu-rasterization',
        '--ignore-gpu-blocklist',
        '--use-gl=angle',
        '--enable-webgl',
        '--enable-accelerated-2d-canvas',
        '--disable-background-timer-throttling'
      ]
    });

    const page = await browser.newPage({
      viewport: { width, height },
      deviceScaleFactor: 1
    });

    const fileUrl = path.isAbsolute(htmlPath) 
      ? `file:///${htmlPath.replace(/\\/g, '/')}`
      : `file:///${path.resolve(process.cwd(), htmlPath).replace(/\\/g, '/')}`;

    await page.goto(fileUrl, { waitUntil: 'networkidle' });

    // Wait for composition initialization
    await page.waitForFunction('window.__READY__ === true', null, { timeout: 10000 });

    // 3. Deterministic frame-stepping loop
    for (let frame = 0; frame < totalFrames; frame++) {
      const t = frame / fps;

      // Evaluate exact timestamp seek
      await page.evaluate(([curT, curFrame]) => {
        if (typeof (window as any).__seek === 'function') {
          (window as any).__seek(curT, curFrame);
        }
      }, [t, frame]);

      // Capture screenshot frame
      const buffer = await page.screenshot({ type: 'png' });
      ff.stdin.write(buffer);
      await ff.stdin.flush();

      if (frame % Math.max(1, Math.floor(fps / 2)) === 0 || frame === totalFrames - 1) {
        const percent = Math.floor((frame / totalFrames) * 100);
        onProgress?.(percent, `Frame ${frame + 1}/${totalFrames} (${t.toFixed(2)}s / ${duration.toFixed(2)}s)`);
      }
    }

    // 4. Finalize streams
    ff.stdin.end();
    await browser.close();

    const exitCode = await ff.exited;
    if (exitCode !== 0) {
      throw new Error(`FFmpeg exited with error code ${exitCode}`);
    }

    return outputPath;
  }
}
