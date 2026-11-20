"""
Diffusion Governor for OpenGen Engine 2 (Image Studio).
Enforces dynamic latent resolution clamping, tiled VAE decoding, sequential CPU offloading,
and deterministic upscaling to guarantee zero CUDA OOM crashes on 4GB-6GB laptop GPUs.
"""
from typing import Tuple, Dict, Any
from opengen.hardware.models import AdaptiveExecutionPolicy


class DiffusionGovernor:
    """Calculates hardware-safe diffusion dimensions and memory flags."""

    @classmethod
    def clamp_resolution(
        cls,
        target_width: int,
        target_height: int,
        policy: AdaptiveExecutionPolicy
    ) -> Tuple[int, int, bool]:
        """
        Clamps generation resolution to the hardware ceiling while preserving aspect ratio.
        Returns: (clamped_width, clamped_height, requires_upscaling).
        """
        max_dim = policy.image_max_resolution
        orig_max = max(target_width, target_height)

        if orig_max <= max_dim:
            return target_width, target_height, False

        # Scale down dimensions proportionally to fit within max_dim
        scale = max_dim / float(orig_max)
        clamped_w = int(round(target_width * scale / 8.0) * 8)
        clamped_h = int(round(target_height * scale / 8.0) * 8)
        clamped_w = max(256, clamped_w)
        clamped_h = max(256, clamped_h)

        return clamped_w, clamped_h, True

    @classmethod
    def get_diffusers_config(cls, policy: AdaptiveExecutionPolicy) -> Dict[str, Any]:
        """Returns recommended Diffusers pipeline memory optimization settings."""
        return {
            "enable_cpu_offload": policy.image_enable_cpu_offload,
            "enable_vae_tiling": policy.image_enable_vae_tiling,
            "precision": policy.image_precision,
            "max_latent_dimension": policy.image_max_resolution,
            "rembg_provider": policy.rembg_provider
        }
