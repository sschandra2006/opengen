"""
Unified Audio & Voiceover Generation Engine for OpenGen.
Provides zero-shot conversational speech synthesis, VoiceStudio integration,
dynamic punctuation timing, and broadcast EBU R128 (-14 LUFS) mastering.
"""
import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from opengen.config import settings
from opengen.engines.audio.timing import AudioTimingDirector

logger = logging.getLogger(__name__)

VOICESTUDIO_API = os.getenv("VOICESTUDIO_API_URL", "http://127.0.0.1:3900")


class AudioEngine:
    """Master generation engine for voiceover, narration, and audio mastering."""

    @classmethod
    def generate_speech(
        cls,
        text: str,
        voice: str = "narrator",
        output_path: Optional[str] = None,
        apply_dsp_mastering: bool = True,
        style: str = "conversational"
    ) -> str:
        """
        Synthesizes speech using VoiceStudio local daemon, edge-tts, or procedural fallback,
        applying dynamic punctuation-based timing and broadcast EBU R128 DSP mastering.
        """
        if not text or not text.strip():
            raise ValueError("Speech synthesis text cannot be empty.")

        if output_path:
            out_file = Path(output_path).resolve()
            out_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            _, run_dir = settings.allocate_run_dir("audio")
            out_file = run_dir / "voiceover.mp3"

        # Apply conversational prosody and punctuation timing
        script = AudioTimingDirector.format_conversational_script(text, style=style)
        raw_out = str(out_file.with_name(f"{out_file.stem}_raw.mp3"))

        generated = False

        # Attempt 1: VoiceStudio REST API daemon
        try:
            import httpx
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"{VOICESTUDIO_API}/v1/audio/speech",
                    json={"model": "kokoro", "input": script, "voice": voice}
                )
                if res.status_code == 200:
                    with open(raw_out, "wb") as f:
                        f.write(res.content)
                    generated = True
                    logger.info("Speech generated via VoiceStudio local daemon.")
        except Exception:
            pass

        # Attempt 2: edge-tts fallback
        if not generated:
            try:
                import edge_tts
                import asyncio
                async def _run():
                    comm = edge_tts.Communicate(script, "en-US-GuyNeural")
                    await comm.save(raw_out)
                asyncio.run(_run())
                if os.path.exists(raw_out) and os.path.getsize(raw_out) > 0:
                    generated = True
                    logger.info("Speech generated via edge-tts.")
            except Exception:
                pass

        # Attempt 3: Procedural FFmpeg tone for local test environments
        if not generated:
            ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
            words_count = max(1, len(text.split()))
            estimated_duration = max(2.0, words_count * 0.4)
            cmd = [
                ffmpeg_bin, "-y",
                "-f", "lavfi",
                "-i", f"sine=frequency=220:duration={estimated_duration}",
                "-af", "afade=t=out:st=1.5:d=0.5",
                "-q:a", "2",
                raw_out
            ]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                generated = True
            except Exception:
                Path(raw_out).touch()

        # DSP Mastering Chain: High-Pass 80Hz + EBU R128 (-14 LUFS, -1.5 dBTP)
        if apply_dsp_mastering and os.path.exists(raw_out) and os.path.getsize(raw_out) > 0:
            cls.master_voice_track(raw_out, str(out_file))
            try:
                if os.path.exists(raw_out) and raw_out != str(out_file):
                    os.remove(raw_out)
            except OSError:
                pass
        else:
            if raw_out != str(out_file):
                shutil.copy2(raw_out, str(out_file))

        return str(out_file)

    @classmethod
    def master_voice_track(cls, input_audio_path: str, output_audio_path: str) -> str:
        """
        Applies modern DSP voice chain:
        1. High-pass filter at 80 Hz (strips mic proximity boom and sub-bass rumble).
        2. EBU R128 Loudness Normalization to -14 LUFS with -1.5 dBTP ceiling.
        """
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        cmd = [
            ffmpeg_bin, "-y",
            "-i", input_audio_path,
            "-af", "highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:a", "libmp3lame" if output_audio_path.endswith(".mp3") else "aac",
            "-b:a", "192k",
            output_audio_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return output_audio_path
        except Exception:
            shutil.copy2(input_audio_path, output_audio_path)
            return output_audio_path


audio_engine = AudioEngine()
