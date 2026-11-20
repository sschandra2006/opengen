"""
OneTake Smart Jump-Cutter & Punch-In Engine (Engine 5 Ecosystem Adapter).
Adapted from artbyjazi/autoclip and OneTake AI:
Surgically cuts dead pauses (>0.35s) and injects alternating camera punch-ins
(1.0x wide <-> 1.25x close-up) on speech boundaries to boost social viewer retention.
Supports Faster-Whisper with automatic fallback to FFmpeg silencedetect.
"""
import os
import re
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class OneTakeCutter:
    """Removes dead air and injects dynamic punch-ins on speech segments."""

    def __init__(self, whisper_model: str = "base"):
        self.whisper_model_name = whisper_model
        self._whisper_model = None

    def _get_speech_ranges_whisper(self, input_video: str, silence_thresh_sec: float) -> Optional[List[Tuple[float, float]]]:
        """Attempts transcription with Faster-Whisper if available."""
        try:
            from faster_whisper import WhisperModel
            if self._whisper_model is None:
                self._whisper_model = WhisperModel(self.whisper_model_name, device="cpu", compute_type="int8")
            segments, _ = self._whisper_model.transcribe(input_video, word_timestamps=True)
            speech_ranges: List[Tuple[float, float]] = []
            for s in segments:
                if s.end - s.start > 0.2:
                    speech_ranges.append((round(s.start, 3), round(s.end, 3)))
            return speech_ranges if speech_ranges else None
        except Exception as e:
            logger.debug(f"Whisper transcription unavailable or failed: {e}. Falling back to FFmpeg silencedetect.")
            return None

    def _get_speech_ranges_ffmpeg(self, input_video: str, silence_thresh_sec: float = 0.35, noise_db: float = -30.0) -> List[Tuple[float, float]]:
        """Detects speech intervals by inverting FFmpeg silencedetect intervals."""
        cmd = [
            "ffmpeg", "-i", input_video,
            "-af", f"silencedetect=noise={noise_db}dB:d={silence_thresh_sec}",
            "-f", "null", "-"
        ]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, text=True, errors="replace")
        output = res.stderr

        silence_starts = [float(m.group(1)) for m in re.finditer(r"silence_start:\s*([\d\.]+)", output)]
        silence_ends = [float(m.group(1)) for m in re.finditer(r"silence_end:\s*([\d\.]+)", output)]

        # Get total duration
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):([\d\.]+)", output)
        total_duration = 10.0
        if dur_match:
            hours, mins, secs = dur_match.groups()
            total_duration = int(hours) * 3600 + int(mins) * 60 + float(secs)

        if not silence_starts:
            # No silence detected; treat whole clip as one speech segment
            return [(0.0, round(total_duration, 3))]

        speech_ranges: List[Tuple[float, float]] = []
        current_pos = 0.0

        for i, s_start in enumerate(silence_starts):
            if s_start > current_pos + 0.15:
                speech_ranges.append((round(current_pos, 3), round(s_start, 3)))
            if i < len(silence_ends):
                current_pos = silence_ends[i]

        if current_pos < total_duration - 0.15:
            speech_ranges.append((round(current_pos, 3), round(total_duration, 3)))

        return speech_ranges or [(0.0, round(total_duration, 3))]

    def detect_speech_ranges(self, input_video: str, silence_thresh_sec: float = 0.35) -> List[Tuple[float, float]]:
        """Identifies active speech intervals via Whisper or FFmpeg."""
        ranges = self._get_speech_ranges_whisper(input_video, silence_thresh_sec)
        if ranges is None:
            ranges = self._get_speech_ranges_ffmpeg(input_video, silence_thresh_sec)
        return ranges

    def process_talking_head(
        self,
        input_video: str,
        output_video: str,
        silence_thresh_sec: float = 0.35,
        zoom_punch_scale: float = 1.25
    ) -> str:
        """
        Removes silent pauses and applies alternating 1.0x / 1.25x camera punch-ins.
        Returns the path to the processed MP4.
        """
        in_path = Path(input_video).resolve()
        out_path = Path(output_video).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if not in_path.exists():
            raise FileNotFoundError(f"Input video not found: {in_path}")

        speech_ranges = self.detect_speech_ranges(str(in_path), silence_thresh_sec)
        if not speech_ranges:
            shutil.copy2(str(in_path), str(out_path))
            return str(out_path)

        # Build FFmpeg select filtergraph with alternating zoom punch-ins
        filter_parts = []
        concat_v = []
        concat_a = []

        for i, (start, end) in enumerate(speech_ranges):
            # Alternate between wide (1.0x) and close-up punch-in (zoom_punch_scale)
            scale = zoom_punch_scale if (i % 2 == 1) else 1.0
            zoom_filter = f"scale=iw*{scale}:ih*{scale},crop=iw/{scale}:ih/{scale}" if scale > 1.0 else "null"

            filter_parts.append(
                f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,{zoom_filter}[v{i}];"
                f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}];"
            )
            concat_v.append(f"[v{i}]")
            concat_a.append(f"[a{i}]")

        n = len(speech_ranges)
        filter_complex = (
            "".join(filter_parts) +
            "".join(concat_v) + f"concat=n={n}:v=1:a=0[outv];" +
            "".join(concat_a) + f"concat=n={n}:v=0:a=1[outa]"
        )

        cmd = [
            "ffmpeg", "-y", "-i", str(in_path),
            "-filter_complex", filter_complex,
            "-map", "[outv]", "-map", "[outa]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            str(out_path)
        ]

        logger.info(f"Executing OneTake jump-cut filtergraph ({n} speech segments)...")
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.warning(f"OneTake FFmpeg filtergraph failed: {res.stderr}. Using copy fallback.")
            shutil.copy2(str(in_path), str(out_path))

        return str(out_path)
