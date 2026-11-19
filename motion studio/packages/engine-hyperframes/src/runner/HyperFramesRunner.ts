import { spawn } from 'node:child_process';
import * as path from 'node:path';
import * as fs from 'node:fs';

export interface HyperFramesRenderOptions {
  compositionPath: string;
  outputPath: string;
  fps?: number;
  crf?: number;
  onProgress?: (percent: number, message: string) => void;
}

export class HyperFramesRunner {
  public static async renderToMp4(options: HyperFramesRenderOptions): Promise<string> {
    const { compositionPath, outputPath, fps = 30, crf = 18, onProgress } = options;

    const outDir = path.dirname(outputPath);
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    const args = [
      'hyperframes',
      'render',
      '-c', compositionPath,
      '-o', outputPath,
      '--fps', String(fps),
      '--crf', String(crf)
    ];

    return new Promise((resolve, reject) => {
      // Use npx on Windows/Linux
      const proc = spawn('npx.cmd', args, {
        cwd: process.cwd(),
        shell: true
      });

      let stdout = '';
      let stderr = '';

      proc.stdout?.on('data', (data) => {
        const text = data.toString();
        stdout += text;
        if (text.includes('%') || text.includes('Render') || text.includes('Frame')) {
          onProgress?.(50, text.trim());
        }
      });

      proc.stderr?.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        if (code === 0 && fs.existsSync(outputPath)) {
          resolve(outputPath);
        } else {
          // If npx.cmd fails, try npx bare
          const fallbackProc = spawn('npx', args, {
            cwd: process.cwd(),
            shell: true
          });

          fallbackProc.on('close', (fbCode) => {
            if (fbCode === 0 && fs.existsSync(outputPath)) {
              resolve(outputPath);
            } else {
              reject(new Error(`HyperFrames render failed with code ${fbCode || code}. Stderr: ${stderr}`));
            }
          });
        }
      });

      proc.on('error', (err) => {
        reject(err);
      });
    });
  }
}
