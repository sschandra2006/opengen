import { Scene } from '@opengen/core';
import * as crypto from 'node:crypto';
import * as path from 'node:path';
import * as fs from 'node:fs';

export class FrameCache {
  private cacheDir: string;

  constructor(cacheDir?: string) {
    this.cacheDir = cacheDir || path.resolve(process.cwd(), 'out', 'cache', 'scenes');
    if (!fs.existsSync(this.cacheDir)) {
      fs.mkdirSync(this.cacheDir, { recursive: true });
    }
  }

  public getSceneHash(scene: Scene, extraSalt: string = ''): string {
    // Incorporate media file mtime/size signatures to auto-invalidate cache when source files change
    let assetSignatures = '';
    if (scene.layers) {
      for (const layer of scene.layers) {
        const src = (layer as any).src || (layer as any).videoSrc || (layer as any).imageSrc;
        if (src && typeof src === 'string' && fs.existsSync(src)) {
          try {
            const stat = fs.statSync(src);
            assetSignatures += `|${src}:${stat.mtimeMs}:${stat.size}`;
          } catch {
            // ignore
          }
        }
      }
    }
    if (scene.audioTracks) {
      for (const track of scene.audioTracks) {
        if (track.src && fs.existsSync(track.src)) {
          try {
            const stat = fs.statSync(track.src);
            assetSignatures += `|${track.src}:${stat.mtimeMs}:${stat.size}`;
          } catch {
            // ignore
          }
        }
      }
    }
    const serialized = JSON.stringify(scene) + assetSignatures + extraSalt;
    return crypto.createHash('sha256').update(serialized).digest('hex');
  }

  public getCachedPath(hash: string): string {
    return path.join(this.cacheDir, `${hash}.mp4`);
  }

  public has(hash: string): boolean {
    const p = this.getCachedPath(hash);
    return fs.existsSync(p) && fs.statSync(p).size > 1024;
  }

  public store(hash: string, sourcePath: string): void {
    const target = this.getCachedPath(hash);
    fs.copyFileSync(sourcePath, target);
  }
}
