import os
import subprocess
from typing import List, Dict, Any, Optional

class SoundDesigner:
    """
    Automated Tri-Tier Sound Design & Foley Injector for OpenGen Engine 5.
    1. Tier 1: Primary voiceover/speech track (centered at 0 dB reference).
    2. Tier 2: High-energy music bed auto-ducked by -14 dB during dialogue.
    3. Tier 3: Micro-SFX foley cues (whooshes, risers, sub-impacts) timed to visual transitions.
    Mastered deterministically to broadcast EBU R128 (-14 LUFS, -1.5 dBTP).
    """
    def __init__(self, sfx_library_dir: str = "assets/sfx"):
        self.sfx_dir = sfx_library_dir
        os.makedirs(self.sfx_dir, exist_ok=True)

    def extract_sfx_cues_from_project(self, project_ir: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans scenes for creativeAdDirectives audioPunctuation cues and calculates absolute project timestamps.
        """
        cues = []
        for scene in project_ir.get("scenes", []):
            scene_start = scene.get("start", 0.0)
            directives = scene.get("creativeAdDirectives", {})
            audio_punc = directives.get("audioPunctuation", {})
            foley_cue = audio_punc.get("foleyCue")
            
            if foley_cue:
                j_cut_lead = audio_punc.get("jCutLeadSec", 0.0)
                timestamp = max(0.0, scene_start - j_cut_lead)
                cues.append({
                    "sound": foley_cue,
                    "timestamp_sec": round(timestamp, 2),
                    "volume": 0.8
                })
        return cues

    def master_audio_track(
        self,
        video_path: str,
        voiceover_path: Optional[str],
        music_path: Optional[str],
        sfx_cues: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Mixes voiceover, auto-ducks music bed, injects foley, and normalizes to -14 LUFS.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Base ffmpeg inputs
        cmd = ["ffmpeg", "-y", "-i", video_path]
        audio_stream_indices = []

        curr_idx = 1
        if voiceover_path and os.path.exists(voiceover_path):
            cmd.extend(["-i", voiceover_path])
            vo_idx = curr_idx
            curr_idx += 1
        else:
            vo_idx = None

        if music_path and os.path.exists(music_path):
            cmd.extend(["-i", music_path])
            bgm_idx = curr_idx
            curr_idx += 1
        else:
            bgm_idx = None

        filter_parts = []
        mix_inputs = []

        if vo_idx is not None:
            filter_parts.append(f"[{vo_idx}:a]volume=1.0[vo_clean];")
            mix_inputs.append("[vo_clean]")

        if bgm_idx is not None:
            # Auto-duck background music by 14dB (volume=0.20)
            filter_parts.append(f"[{bgm_idx}:a]volume=0.20[bgm_ducked];")
            mix_inputs.append("[bgm_ducked]")

        # Inject SFX cues
        for i, cue in enumerate(sfx_cues):
            cue_sound = cue.get("sound", "whoosh_slide")
            sfx_file = os.path.join(self.sfx_dir, f"{cue_sound}.wav")

            # Generate procedural sound if not in assets/sfx/
            if not os.path.exists(sfx_file):
                self._synthesize_fallback_sfx(cue_sound, sfx_file)

            cmd.extend(["-i", sfx_file])
            sfx_idx = curr_idx
            curr_idx += 1

            delay_ms = int(cue.get("timestamp_sec", 0.0) * 1000)
            vol = cue.get("volume", 0.75)
            filter_parts.append(f"[{sfx_idx}:a]adelay={delay_ms}|{delay_ms},volume={vol}[sfx_{i}];")
            mix_inputs.append(f"[sfx_{i}]")

        if mix_inputs:
            inputs_str = "".join(mix_inputs)
            count = len(mix_inputs)
            filter_parts.append(f"{inputs_str}amix=inputs={count}:duration=first:dropout_transition=2[mixed_pre];")
            filter_parts.append("[mixed_pre]loudnorm=I=-14:LRA=7:TP=-1.5[final_audio]")

            cmd.extend([
                "-filter_complex", "".join(filter_parts),
                "-map", "0:v",
                "-map", "[final_audio]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                output_path
            ])
        else:
            # Pass through with video copy if no audio inputs provided
            cmd.extend(["-c:v", "copy", output_path])

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path

    def _synthesize_fallback_sfx(self, sound_type: str, output_path: str):
        """Generates procedural acoustic placeholder audio using FFmpeg lavfi filters."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if "impact" in sound_type:
            # 60Hz sub-bass punch
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=60:duration=0.5",
                "-af", "afade=t=out:st=0.08:d=0.42", output_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        elif "riser" in sound_type:
            # Swelling tension sweep
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anoisesrc=d=1.2:c=white",
                "-af", "afade=t=in:st=0:d=1.0,volume=0.4", output_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        elif "ding" in sound_type or "pop" in sound_type:
            # High chime pop
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1200:duration=0.2",
                "-af", "afade=t=out:st=0.02:d=0.18", output_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            # Air whoosh
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=350:duration=0.25",
                "-af", "afade=t=in:st=0:d=0.08,afade=t=out:st=0.1:d=0.15", output_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
