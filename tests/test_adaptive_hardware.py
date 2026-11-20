"""
Unit and integration tests for OpenGen Adaptive Hardware Governance.
Verifies system auditing, 4-tier classification, policy generation,
token budgeting, diffusion memory clamping, video encoder selection, and MemoryGuard.
"""
import pytest
from opengen.hardware.models import (
    HardwareTier,
    AcceleratorType,
    HardwareProfile,
    AdaptiveExecutionPolicy,
)
from opengen.hardware.auditor import HardwareAuditor
from opengen.hardware.classifier import TierClassifier
from opengen.hardware.token_budgeter import TokenBudgeter
from opengen.hardware.diffusion_governor import DiffusionGovernor
from opengen.hardware.video_governor import VideoGovernor
from opengen.hardware.memory_guard import MemoryGuard, HardwareMemoryError
from opengen.hardware.governor import AdaptiveGovernor
from opengen.client import OpenGenClient
from opengen.mcp.server import tool_get_hardware_profile


def test_hardware_auditor_live():
    """Verifies that the live hardware auditor interrogates host resources without error."""
    profile = HardwareAuditor.audit()
    assert profile.total_ram_gb > 0
    assert profile.available_ram_gb > 0
    assert profile.cpu_count_physical >= 1
    assert profile.cpu_count_logical >= 1
    assert profile.accelerator in [
        AcceleratorType.CUDA,
        AcceleratorType.MPS,
        AcceleratorType.DIRECTML,
        AcceleratorType.ROCM,
        AcceleratorType.CPU_ONLY,
    ]


def test_tier_classifier_mapping():
    """Verifies deterministic hardware tier classification across the 4 operational tiers."""
    # Tier 0: Potato / Ultra-Light (4GB RAM, 0 VRAM)
    p0 = HardwareProfile(
        total_ram_gb=4.0,
        available_ram_gb=1.8,
        cpu_count_physical=2,
        cpu_count_logical=4,
        accelerator=AcceleratorType.CPU_ONLY,
        total_vram_gb=0.0,
        free_vram_gb=0.0,
        assigned_tier=HardwareTier.TIER_0_POTATO,
    )
    assert TierClassifier.classify(p0) == HardwareTier.TIER_0_POTATO

    # Tier 1: Budget Laptop (16GB RAM, 4GB RTX 3050)
    p1 = HardwareProfile(
        total_ram_gb=15.7,
        available_ram_gb=4.5,
        cpu_count_physical=8,
        cpu_count_logical=16,
        accelerator=AcceleratorType.CUDA,
        gpu_name="NVIDIA GeForce RTX 3050 Laptop GPU",
        total_vram_gb=4.0,
        free_vram_gb=3.8,
        assigned_tier=HardwareTier.TIER_1_BUDGET,
    )
    assert TierClassifier.classify(p1) == HardwareTier.TIER_1_BUDGET

    # Tier 2: Mid-Pro Workstation (32GB RAM, 8GB RTX 4070)
    p2 = HardwareProfile(
        total_ram_gb=31.8,
        available_ram_gb=18.0,
        cpu_count_physical=12,
        cpu_count_logical=24,
        accelerator=AcceleratorType.CUDA,
        gpu_name="NVIDIA GeForce RTX 4070",
        total_vram_gb=8.0,
        free_vram_gb=7.5,
        assigned_tier=HardwareTier.TIER_2_PRO,
    )
    assert TierClassifier.classify(p2) == HardwareTier.TIER_2_PRO

    # Tier 3: AI Studio Server (64GB RAM, 24GB RTX 4090)
    p3 = HardwareProfile(
        total_ram_gb=63.8,
        available_ram_gb=45.0,
        cpu_count_physical=16,
        cpu_count_logical=32,
        accelerator=AcceleratorType.CUDA,
        gpu_name="NVIDIA GeForce RTX 4090",
        total_vram_gb=24.0,
        free_vram_gb=22.0,
        assigned_tier=HardwareTier.TIER_3_STUDIO,
    )
    assert TierClassifier.classify(p3) == HardwareTier.TIER_3_STUDIO


def test_battery_downshift():
    """Verifies that running on battery power steps down the tier to prevent thermal throttling."""
    p_battery = HardwareProfile(
        total_ram_gb=31.8,
        available_ram_gb=18.0,
        cpu_count_physical=8,
        cpu_count_logical=16,
        accelerator=AcceleratorType.CUDA,
        total_vram_gb=8.0,
        free_vram_gb=7.5,
        is_battery_powered=True,
        assigned_tier=HardwareTier.TIER_2_PRO,
    )
    # Would normally be Tier 2, but battery shifts it down to Tier 1
    assert TierClassifier.classify(p_battery) == HardwareTier.TIER_1_BUDGET


def test_policy_generation():
    """Verifies that execution policies enforce strict memory and token boundaries."""
    p0 = HardwareProfile(
        total_ram_gb=6.0,
        available_ram_gb=2.0,
        cpu_count_physical=2,
        cpu_count_logical=4,
        accelerator=AcceleratorType.CPU_ONLY,
        assigned_tier=HardwareTier.TIER_0_POTATO,
    )
    pol0 = TierClassifier.generate_policy(p0)
    assert pol0.max_llm_context == 2048
    assert pol0.max_output_tokens == 768
    assert pol0.image_max_resolution == 512
    assert pol0.video_resolution == "720x1280"
    assert pol0.video_target_fps == 24
    assert pol0.doc_chunk_size == 6

    p1 = HardwareProfile(
        total_ram_gb=16.0,
        available_ram_gb=5.0,
        cpu_count_physical=8,
        cpu_count_logical=16,
        accelerator=AcceleratorType.CUDA,
        has_nvenc=True,
        assigned_tier=HardwareTier.TIER_1_BUDGET,
    )
    pol1 = TierClassifier.generate_policy(p1)
    assert pol1.max_llm_context == 4096
    assert pol1.max_output_tokens == 1536
    assert pol1.image_max_resolution == 768
    assert pol1.image_enable_cpu_offload is True
    assert pol1.image_enable_vae_tiling is True
    assert pol1.ffmpeg_codec == "h264_nvenc"
    assert pol1.video_target_fps == 30


def test_token_budgeter_and_chunking():
    """Verifies token clamping and sequence chunking logic."""
    pol1 = AdaptiveExecutionPolicy(tier=HardwareTier.TIER_1_BUDGET, max_output_tokens=1536)

    # User asks for 8000 tokens, clamped to 1536
    clamped = TokenBudgeter.clamp_max_output_tokens(pol1, requested_max_tokens=8000)
    assert clamped == 1536

    # User asks for 1000 tokens, respects 1000 since it is below 1536
    assert TokenBudgeter.clamp_max_output_tokens(pol1, requested_max_tokens=1000) == 1000

    # Sequence chunking
    items = list(range(25))
    chunks = TokenBudgeter.chunk_sequence(items, chunk_size_override=10)
    assert len(chunks) == 3
    assert len(chunks[0]) == 10
    assert len(chunks[1]) == 10
    assert len(chunks[2]) == 5


def test_diffusion_governor_resolution_clamping():
    """Verifies that large requested diffusion resolutions are clamped safely."""
    pol1 = AdaptiveExecutionPolicy(tier=HardwareTier.TIER_1_BUDGET, image_max_resolution=768)

    # 1024x1024 requested on Tier 1 (768 cap)
    cw, ch, needs_up = DiffusionGovernor.clamp_resolution(1024, 1024, pol1)
    assert cw <= 768
    assert ch <= 768
    assert needs_up is True
    assert cw == ch  # Aspect ratio preserved

    # 512x512 requested on Tier 1 (768 cap) -> no downscaling needed
    cw, ch, needs_up = DiffusionGovernor.clamp_resolution(512, 512, pol1)
    assert cw == 512
    assert ch == 512
    assert needs_up is False


def test_video_governor_aspect_ratios():
    """Verifies video governor calculates correct dimensions for different aspect ratios."""
    pol1 = AdaptiveExecutionPolicy(
        tier=HardwareTier.TIER_1_BUDGET,
        video_resolution="1080x1920",
        video_target_fps=30,
        ffmpeg_codec="h264_nvenc",
        ffmpeg_threads=4,
    )

    # Vertical 9:16
    v_9_16 = VideoGovernor.get_render_parameters(pol1, aspect_ratio="9:16")
    assert v_9_16["width"] == 1080
    assert v_9_16["height"] == 1920
    assert v_9_16["fps"] == 30
    assert v_9_16["codec"] == "h264_nvenc"

    # Landscape 16:9
    v_16_9 = VideoGovernor.get_render_parameters(pol1, aspect_ratio="16:9")
    assert v_16_9["width"] == 1920
    assert v_16_9["height"] == 1080

    # Square 1:1
    v_1_1 = VideoGovernor.get_render_parameters(pol1, aspect_ratio="1:1")
    assert v_1_1["width"] == 1080
    assert v_1_1["height"] == 1080


def test_memory_guard_circuit_breaker():
    """Verifies MemoryGuard context manager execution and OOM interception."""
    # Normal execution
    with MemoryGuard(operation_name="test_normal") as guard:
        x = 42
    assert x == 42

    # Interception of simulated memory exhaustion
    with pytest.raises(HardwareMemoryError) as exc_info:
        with MemoryGuard(operation_name="test_oom"):
            raise MemoryError("Simulated host memory exhaustion")
    assert "test_oom" in str(exc_info.value)
    assert "exhaustion" in str(exc_info.value)


def test_client_hardware_interface():
    """Verifies OpenGenClient exposes client.hardware telemetry interface cleanly."""
    client = OpenGenClient()
    profile_data = client.hardware.get_profile()
    assert "total_ram_gb" in profile_data
    assert "assigned_tier" in profile_data

    policy_data = client.hardware.get_policy()
    assert "max_llm_context" in policy_data
    assert "max_output_tokens" in policy_data


def test_mcp_hardware_tool():
    """Verifies FastMCP hardware profile tool returns structured status."""
    res = tool_get_hardware_profile()
    assert res["status"] == "completed"
    assert "profile" in res
    assert "policy" in res
