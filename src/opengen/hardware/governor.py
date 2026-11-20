"""
Central Adaptive Hardware Governor for OpenGen.
Provides high-level coordinator methods to retrieve tailored parameters,
token budgets, resolution caps, and memory guards across all 5 OpenGen engines.
"""
import logging
import os
from typing import Optional, Tuple, Dict, Any, List

from opengen.hardware.models import (
    HardwareProfile, HardwareTier, AdaptiveExecutionPolicy
)
from opengen.hardware.auditor import HardwareAuditor
from opengen.hardware.classifier import TierClassifier
from opengen.hardware.token_budgeter import TokenBudgeter
from opengen.hardware.diffusion_governor import DiffusionGovernor
from opengen.hardware.video_governor import VideoGovernor
from opengen.hardware.memory_guard import MemoryGuard

logger = logging.getLogger(__name__)


class AdaptiveGovernor:
    """Master hardware governance controller for OpenGen."""

    def __init__(self, tier_override: Optional[HardwareTier] = None):
        self._tier_override = tier_override
        self._profile: Optional[HardwareProfile] = None
        self._policy: Optional[AdaptiveExecutionPolicy] = None
        self.refresh()

    def refresh(self):
        """Re-audits system hardware and re-calculates the active execution policy."""
        profile = HardwareAuditor.audit()

        # Check for environment variable override (e.g. OPENGEN_HARDWARE_TIER=tier_0_potato)
        env_tier_str = os.environ.get("OPENGEN_HARDWARE_TIER")
        if env_tier_str:
            try:
                self._tier_override = HardwareTier(env_tier_str.lower().strip())
            except ValueError:
                logger.warning(f"Invalid OPENGEN_HARDWARE_TIER '{env_tier_str}'. Ignoring.")

        # Determine tier
        if self._tier_override:
            profile.assigned_tier = self._tier_override
        else:
            profile.assigned_tier = TierClassifier.classify(profile)

        self._profile = profile
        self._policy = TierClassifier.generate_policy(profile)
        logger.info(
            f"HardwareGovernor initialized: Tier='{profile.assigned_tier.value}', "
            f"RAM={profile.total_ram_gb}GB ({profile.available_ram_gb}GB free), "
            f"GPU='{profile.gpu_name or 'None'}' ({profile.total_vram_gb}GB VRAM)"
        )

    @property
    def profile(self) -> HardwareProfile:
        if self._profile is None:
            self.refresh()
        return self._profile

    @property
    def policy(self) -> AdaptiveExecutionPolicy:
        if self._policy is None:
            self.refresh()
        return self._policy

    def get_token_budget(
        self,
        requested_max_tokens: Optional[int] = None,
        estimated_schema_tokens: int = 500
    ) -> Tuple[int, int]:
        """
        Returns: (clamped_context_window, clamped_max_output_tokens)
        """
        ctx = TokenBudgeter.clamp_context_window(self.policy)
        out = TokenBudgeter.clamp_max_output_tokens(
            self.policy,
            requested_max_tokens=requested_max_tokens,
            estimated_schema_tokens=estimated_schema_tokens
        )
        return ctx, out

    def get_image_plan(
        self,
        target_width: int = 1024,
        target_height: int = 1024
    ) -> Tuple[int, int, bool, Dict[str, Any]]:
        """
        Returns: (clamped_width, clamped_height, requires_upscaling, diffusers_kwargs)
        """
        w, h, needs_up = DiffusionGovernor.clamp_resolution(
            target_width=target_width,
            target_height=target_height,
            policy=self.policy
        )
        diff_cfg = DiffusionGovernor.get_diffusers_config(self.policy)
        return w, h, needs_up, diff_cfg

    def get_video_plan(self, aspect_ratio: str = "9:16") -> Dict[str, Any]:
        """Returns video render dimensions, framerate, and FFmpeg encoder settings."""
        return VideoGovernor.get_render_parameters(self.policy, aspect_ratio=aspect_ratio)

    def get_document_plan(self) -> Dict[str, Any]:
        """Returns document chunk size and preferred reference extractor."""
        return {
            "chunk_size": self.policy.doc_chunk_size,
            "preferred_extractor": self.policy.preferred_doc_extractor,
            "use_lightweight_parser": self.policy.tier in [HardwareTier.TIER_0_POTATO, HardwareTier.TIER_1_BUDGET]
        }

    def get_presentation_plan(self) -> Dict[str, Any]:
        """Returns presentation generation chunking bounds."""
        return {
            "max_slides_per_pass": self.policy.max_slides_per_pass,
            "tier": self.policy.tier
        }

    def guard(self, operation_name: str = "generative_task") -> MemoryGuard:
        """Creates a MemoryGuard context manager for the current hardware tier."""
        return MemoryGuard(operation_name=operation_name)


# Global singleton instance
hardware_governor = AdaptiveGovernor()
