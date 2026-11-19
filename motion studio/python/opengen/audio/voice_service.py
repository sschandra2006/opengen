import os
import subprocess
from typing import List, Dict, Any, Optional

VOICESTUDIO_API = os.getenv("VOICESTUDIO_API_URL", "http://127.0.0.1:3900")

class VoiceService:
    def __init__(self, use_cuda: bool = False):
        self.use_cuda = use_cuda
        self._whisper = None

    def _get_whisper(self):
        if self._whisper is None:
            try:
                from faster_whisper import WhisperModel
                device = "cuda" if self.use_cuda else "cpu"
                compute_type = "float16" if self.use_cuda else "int8"
                self._whisper = WhisperModel("tiny", device=device, compute_type=compute_type)
            except Exception as e:
                print(f"[VoiceService] Whisper initialization notice: {e}")
                self._whisper = False
        return self._whisper

    def generate_speech(self, text: str, voice: str = "narrator", output_path: str = "out/voice.mp3") -> str:
        """
        Synthesize speech using VoiceStudio API or local edge-tts / Kokoro fallback.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Attempt 1: VoiceStudio REST API
        try:
            import requests
            res = requests.post(
                f"{VOICESTUDIO_API}/v1/audio/speech",
                json={"model": "kokoro", "input": text, "voice": voice},
                timeout=5
            )
            if res.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(res.content)
                return output_path
        except Exception:
            pass

        # Attempt 2: edge-tts (fast, crisp, high-quality local CLI/module)
        try:
            import edge_tts
            import asyncio
            async def _run():
                communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
                await communicate.save(output_path)
            asyncio.run(_run())
            if os.path.exists(output_path):
                return output_path
        except Exception:
            pass

        # Attempt 3: FFmpeg tone placeholder
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-q:a", "2", output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return output_path

    def align_transcript(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Extract word-level timestamps using Faster-Whisper.
        """
        whisper = self._get_whisper()
        if not whisper:
            return []

        segments, _ = whisper.transcribe(audio_path, word_timestamps=True)
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
