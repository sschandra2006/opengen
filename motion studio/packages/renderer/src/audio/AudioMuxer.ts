import * as path from 'node:path';
import * as fs from 'node:fs';

export interface MuxOptions {
  videoTrackPath: string;
  voiceoverTrackPath?: string;
  musicTrackPath?: string;
  outputPath: string;
  targetLUFS?: number;
  truePeak?: number;
}

export class AudioMuxer {
  public static async mux(options: MuxOptions): Promise<string> {
    const {
      videoTrackPath,
      voiceoverTrackPath,
      musicTrackPath,
      outputPath,
      targetLUFS = -14.0,
      truePeak = -1.5
    } = options;

    const outDir = path.dirname(outputPath);
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    // Case 1: Video only, no audio tracks
    if (!voiceoverTrackPath && !musicTrackPath) {
      const proc = Bun.spawn(['ffmpeg', '-y', '-loglevel', 'error', '-i', videoTrackPath, '-c', 'copy', outputPath], {
        stdout: 'ignore',
        stderr: 'inherit'
      });
      const code = await proc.exited;
      if (code !== 0) throw new Error(`FFmpeg copy failed with code ${code}`);
      return outputPath;
    }

    const args: string[] = ['-y', '-loglevel', 'error', '-i', videoTrackPath];
    let filterComplex = '';

    // Case 2: Both Voiceover and Background Music (Auto-ducking + EBU R128)
    if (voiceoverTrackPath && musicTrackPath) {
      args.push('-i', voiceoverTrackPath, '-i', musicTrackPath);
      // Reduce music volume to 0.20 (-14 dB ducking), mix, and normalize
      filterComplex = `[2:a]volume=0.20[bgm];[1:a][bgm]amix=inputs=2:duration=first[mixed];[mixed]loudnorm=I=${targetLUFS}:LRA=7:TP=${truePeak}[aout]`;
    }
    // Case 3: Voiceover only
    else if (voiceoverTrackPath) {
      args.push('-i', voiceoverTrackPath);
      filterComplex = `[1:a]loudnorm=I=${targetLUFS}:LRA=7:TP=${truePeak}[aout]`;
    }
    // Case 4: Music only
    else if (musicTrackPath) {
      args.push('-i', musicTrackPath);
      filterComplex = `[1:a]loudnorm=I=${targetLUFS}:LRA=7:TP=${truePeak}[aout]`;
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

    const proc = Bun.spawn(['ffmpeg', ...args], {
      stdout: 'ignore',
      stderr: 'inherit'
    });

    const code = await proc.exited;
    if (code !== 0 || !fs.existsSync(outputPath)) {
      throw new Error(`FFmpeg audio mastering failed with exit code ${code}`);
    }

    return outputPath;
  }
}
