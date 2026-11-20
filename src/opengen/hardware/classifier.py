"""
Hardware Tier Classifier for OpenGen.
Maps system memory, GPU VRAM, and accelerator availability to optimal operational tiers
and produces tailored execution policies.
"""
import logging
from opengen.hardware.models import (
    HardwareProfile, HardwareTier, AcceleratorType, AdaptiveExecutionPolicy
)

logger = logging.getLogger(__name__)


class TierClassifier:
    """Classifies host hardware and formulates adaptive execution policies."""

    @classmethod
    def classify(cls, profile: HardwareProfile) -> HardwareTier:
        """Determines the appropriate hardware tier based on system constraints."""
        total_ram = profile.total_ram_gb
        vram = profile.total_vram_gb
        accel = profile.accelerator

        # Tier 3: Studio / High-End AI Server (32GB+ RAM and 15GB+ VRAM)
        if total_ram >= 30.0 and vram >= 15.0:
            tier = HardwareTier.TIER_3_STUDIO

        # Tier 2: Mid-Pro Workstation (16GB+ RAM and 7GB+ VRAM, or Apple Silicon with 24GB+ unified)
        elif total_ram >= 15.0 and vram >= 7.0:
            tier = HardwareTier.TIER_2_PRO
        elif accel == AcceleratorType.MPS and total_ram >= 24.0:
            tier = HardwareTier.TIER_2_PRO

        # Tier 1: Budget Laptop (8-16GB RAM and 3.5GB-6.5GB VRAM, or 16GB RAM with iGPU)
        elif (total_ram >= 12.0 and vram >= 3.5) or (total_ram >= 14.0):
            tier = HardwareTier.TIER_1_BUDGET

        # Tier 0: Potato / Ultra-Light (<=8GB RAM or very low available memory)
        else:
            tier = HardwareTier.TIER_0_POTATO

        # If running on battery, step down one tier to prevent thermal throttling & battery drain
        if profile.is_battery_powered:
            if tier == HardwareTier.TIER_3_STUDIO:
                tier = HardwareTier.TIER_2_PRO
            elif tier == HardwareTier.TIER_2_PRO:
                tier = HardwareTier.TIER_1_BUDGET
            elif tier == HardwareTier.TIER_1_BUDGET:
                tier = HardwareTier.TIER_0_POTATO

        return tier

    @classmethod
    def generate_policy(cls, profile: HardwareProfile) -> AdaptiveExecutionPolicy:
        """Generates an AdaptiveExecutionPolicy tailored for the classified tier."""
        tier = profile.assigned_tier

        if tier == HardwareTier.TIER_0_POTATO:
            return AdaptiveExecutionPolicy(
                tier=tier,
                max_llm_context=2048,
                max_output_tokens=768,
                allow_local_llm=False,
                recommended_local_model="ollama/qwen2.5:1.5b",
                recommended_remote_model="gemini/gemini-2.5-flash",
                image_max_resolution=512,
                image_enable_cpu_offload=True,
                image_enable_vae_tiling=True,
                image_precision="int8",
                rembg_provider="cpu",
                video_resolution="720x1280",
                video_target_fps=24,
                ffmpeg_threads=2,
                ffmpeg_codec="libx264",
                doc_chunk_size=6,
                preferred_doc_extractor="pymupdf",
                max_slides_per_pass=5
            )

        elif tier == HardwareTier.TIER_1_BUDGET:
            return AdaptiveExecutionPolicy(
                tier=tier,
                max_llm_context=4096,
                max_output_tokens=1536,
                allow_local_llm=True,
                recommended_local_model="ollama/qwen2.5:7b",
                recommended_remote_model="gemini/gemini-2.5-flash",
                image_max_resolution=768,
                image_enable_cpu_offload=True,
                image_enable_vae_tiling=True,
                image_precision="fp16",
                rembg_provider="cuda" if profile.accelerator == AcceleratorType.CUDA else "cpu",
                video_resolution="1080x1920",
                video_target_fps=30,
                ffmpeg_threads=min(4, max(2, profile.cpu_count_physical)),
                ffmpeg_codec="h264_nvenc" if profile.has_nvenc else "libx264",
                doc_chunk_size=10,
                preferred_doc_extractor="pymupdf",
                max_slides_per_pass=8
            )

        elif tier == HardwareTier.TIER_2_PRO:
            return AdaptiveExecutionPolicy(
                tier=tier,
                max_llm_context=16384,
                max_output_tokens=4096,
                allow_local_llm=True,
                recommended_local_model="ollama/qwen2.5:14b",
                recommended_remote_model="gemini/gemini-2.5-flash",
                image_max_resolution=1024,
                image_enable_cpu_offload=False,
                image_enable_vae_tiling=True,
                image_precision="fp16",
                rembg_provider="cuda" if profile.accelerator == AcceleratorType.CUDA else "cpu",
                video_resolution="1080x1920",
                video_target_fps=60,
                ffmpeg_threads=min(8, max(4, profile.cpu_count_physical)),
                ffmpeg_codec="h264_nvenc" if profile.has_nvenc else "libx264",
                doc_chunk_size=20,
                preferred_doc_extractor="pymupdf",
                max_slides_per_pass=12
            )

        else:  # TIER_3_STUDIO
            return AdaptiveExecutionPolicy(
                tier=tier,
                max_llm_context=65536,
                max_output_tokens=8192,
                allow_local_llm=True,
                recommended_local_model="ollama/qwen2.5:72b",
                recommended_remote_model="anthropic/claude-3-7-sonnet",
                image_max_resolution=2048,
                image_enable_cpu_offload=False,
                image_enable_vae_tiling=False,
                image_precision="fp16",
                rembg_provider="cuda" if profile.accelerator == AcceleratorType.CUDA else "cpu",
                video_resolution="2160x3840",
                video_target_fps=60,
                ffmpeg_threads=min(16, max(8, profile.cpu_count_physical)),
                ffmpeg_codec="h264_nvenc" if profile.has_nvenc else "libx264",
                doc_chunk_size=50,
                preferred_doc_extractor="docling",
                max_slides_per_pass=20
            )
