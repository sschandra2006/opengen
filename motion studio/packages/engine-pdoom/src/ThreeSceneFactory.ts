import { spawn } from 'node:child_process';
import * as path from 'node:path';
import * as fs from 'node:fs';

export interface PdoomRenderOptions {
  from?: number;
  to?: number;
  fps?: number;
  landscape?: boolean;
  outputPath: string;
  onProgress?: (percent: number, msg: string) => void;
}

export class ThreeSceneFactory {
  private static getPdoomAppPath(): string {
    return path.resolve(process.cwd(), 'pdoom-video', 'app');
  }

  public static async renderPdoomScene(options: PdoomRenderOptions): Promise<string> {
    const { from = 0, to = 5, fps = 30, landscape = false, outputPath, onProgress } = options;
    const pdoomApp = this.getPdoomAppPath();
    const renderScript = path.join(pdoomApp, 'scripts', 'render.ts');

    const outDir = path.dirname(outputPath);
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    const args = [
      renderScript,
      'video',
      '--from', String(from),
      '--to', String(to),
      '--fps', String(fps),
      '--out', outputPath
    ];

    if (landscape) {
      args.push('--landscape');
    }

    return new Promise((resolve, reject) => {
      const proc = spawn('bun', args, {
        cwd: pdoomApp,
        shell: true
      });

      let stderr = '';

      proc.stdout?.on('data', (data) => {
        const text = data.toString();
        if (text.includes('frame') || text.includes('Render') || text.includes('%')) {
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
          reject(new Error(`pdoom-video render failed with exit code ${code}. Stderr: ${stderr}`));
        }
      });

      proc.on('error', (err) => {
        reject(err);
      });
    });
  }

  public static async renderContactSheet(
    from: number,
    to: number,
    n: number = 16,
    cols: number = 4,
    outputPath: string
  ): Promise<string> {
    const pdoomApp = this.getPdoomAppPath();
    const renderScript = path.join(pdoomApp, 'scripts', 'render.ts');

    const args = [
      renderScript,
      'sheet',
      '--from', String(from),
      '--to', String(to),
      '--n', String(n),
      '--cols', String(cols),
      '--out', outputPath
    ];

    return new Promise((resolve, reject) => {
      const proc = spawn('bun', args, { cwd: pdoomApp, shell: true });
      proc.on('close', (code) => {
        if (code === 0 && fs.existsSync(outputPath)) {
          resolve(outputPath);
        } else {
          reject(new Error(`Contact sheet render failed with exit code ${code}`));
        }
      });
      proc.on('error', reject);
    });
  }
}
