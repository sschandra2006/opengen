"""
Video Governor for OpenGen Engine 4 (Motion Graphics Studio).
Selects optimal hardware video encoders, framerates, and render dimensions
to ensure smooth 60fps or 30fps playback without memory thrashing or CPU overheating.
"""
from typing import Dict, Any, Tuple
from opengen.hardware.models import AdaptiveExecutionPolicy


class VideoGovernor:
    """Configures hardware-tailored FFmpeg encoding and resolution parameters."""

    @classmethod
    def get_render_parameters(
        cls,
        policy: AdaptiveExecutionPolicy,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """
        Calculates safe dimensions, framerate, threads, and codec for video rendering.
        """
        res_parts = policy.video_resolution.split("x")
        base_w = int(res_parts[0])
        base_h = int(res_parts[1])

        # Adjust dimensions for aspect ratio
        if aspect_ratio == "16:9":
            w, h = max(base_w, base_h), min(base_w, base_h)
        elif aspect_ratio == "1:1":
            dim = min(base_w, base_h)
            w, h = dim, dim
        else:  # Default to mobile 9:16 vertical
            w, h = min(base_w, base_h), max(base_w, base_h)

        # Codec tune
        codec = policy.ffmpeg_codec
        preset = "p4" if "nvenc" in codec else "veryfast"

        return {
            "width": w,
            "height": h,
            "fps": policy.video_target_fps,
            "codec": codec,
            "threads": policy.ffmpeg_threads,
            "preset": preset,
            "crf": 23 if codec == "libx264" else None
        }
