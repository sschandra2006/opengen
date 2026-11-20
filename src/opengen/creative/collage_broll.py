"""
Collage B-Roll Multi-Panel Mosaic Generator (Engine 5 Ecosystem Adapter).
Adapted from Collage B-Roll & HeroEditKit:
Weaves multiple simultaneous video feeds (e.g. founder talking head, screen recording demo,
customer testimonial, dynamic B-roll) into synchronized 9:16 Bento Box mosaics.
"""
import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class CollageBRollGenerator:
    """Assembles 2 to 4 video feeds into an animated, synchronized Bento Box mosaic."""

    @classmethod
    def render_bento_mosaic(
        cls,
        clips: List[str],
        output_path: str,
        duration: float = 4.0,
        aspect_ratio: str = "9:16",
        background_hex: str = "0x090D16"
    ) -> str:
        """
        Renders multiple video feeds into an animated Bento Box mosaic.
        Supports 2, 3, or 4 input clips.
        """
        if not clips:
            raise ValueError("CollageBRollGenerator requires at least 1 input clip.")

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Validate that all input files exist
        valid_clips = [str(Path(c).resolve()) for c in clips if Path(c).exists()]
        if not valid_clips:
            raise FileNotFoundError(f"None of the provided clips exist: {clips}")

        # If only 1 clip, just trim/scale to vertical 9:16
        if len(valid_clips) == 1:
            cmd = [
                "ffmpeg", "-y", "-i", valid_clips[0],
                "-t", str(duration),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x090D16",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                str(out_path)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
            return str(out_path)

        dur_str = str(duration)
        bg = background_hex

        # Build filtergraph based on clip count
        if len(valid_clips) == 2:
            # 2-Panel Split: Top (1080x960) + Bottom (1080x960)
            filtergraph = (
                f"[0:v]trim=duration={dur_str},scale=1040:920:force_original_aspect_ratio=increase,crop=1040:920,pad=1080:960:20:20:color={bg}[top];"
                f"[1:v]trim=duration={dur_str},scale=1040:920:force_original_aspect_ratio=increase,crop=1040:920,pad=1080:960:20:20:color={bg}[bot];"
                f"[top][bot]vstack=inputs=2[final_mosaic]"
            )
            inputs = ["-i", valid_clips[0], "-i", valid_clips[1]]

        elif len(valid_clips) == 3:
            # 3-Panel Bento: Top Hero (1080x1080) + Bottom Left (540x840) + Bottom Right (540x840)
            filtergraph = (
                f"[0:v]trim=duration={dur_str},scale=1040:1040:force_original_aspect_ratio=increase,crop=1040:1040,pad=1080:1080:20:20:color={bg}[top];"
                f"[1:v]trim=duration={dur_str},scale=500:800:force_original_aspect_ratio=increase,crop=500:800,pad=540:840:20:20:color={bg}[bot_left];"
                f"[2:v]trim=duration={dur_str},scale=500:800:force_original_aspect_ratio=increase,crop=500:800,pad=540:840:20:20:color={bg}[bot_right];"
                f"[bot_left][bot_right]hstack=inputs=2[bottom_row];"
                f"[top][bottom_row]vstack=inputs=2[final_mosaic]"
            )
            inputs = ["-i", valid_clips[0], "-i", valid_clips[1], "-i", valid_clips[2]]

        else:
            # 4-Panel 2x2 Grid (1080x1920)
            filtergraph = (
                f"[0:v]trim=duration={dur_str},scale=500:920:force_original_aspect_ratio=increase,crop=500:920,pad=540:960:20:20:color={bg}[tl];"
                f"[1:v]trim=duration={dur_str},scale=500:920:force_original_aspect_ratio=increase,crop=500:920,pad=540:960:20:20:color={bg}[tr];"
                f"[2:v]trim=duration={dur_str},scale=500:920:force_original_aspect_ratio=increase,crop=500:920,pad=540:960:20:20:color={bg}[bl];"
                f"[3:v]trim=duration={dur_str},scale=500:920:force_original_aspect_ratio=increase,crop=500:920,pad=540:960:20:20:color={bg}[br];"
                f"[tl][tr]hstack=inputs=2[top_row];"
                f"[bl][br]hstack=inputs=2[bot_row];"
                f"[top_row][bot_row]vstack=inputs=2[final_mosaic]"
            )
            inputs = ["-i", valid_clips[0], "-i", valid_clips[1], "-i", valid_clips[2], "-i", valid_clips[3]]

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filtergraph,
            "-map", "[final_mosaic]",
            "-t", dur_str,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            str(out_path)
        ]

        logger.info(f"Rendering {len(valid_clips)}-panel Bento video mosaic...")
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg Bento mosaic render failed: {res.stderr}")

        return str(out_path)
