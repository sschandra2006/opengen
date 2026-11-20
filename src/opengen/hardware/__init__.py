"""
OpenGen Adaptive Hardware & Compute Governance Package.
Provides automated system auditing, dynamic 4-tier laptop classification,
token budgeting, diffusion memory clamping, and zero-crash OOM protection.
"""
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
from opengen.hardware.governor import AdaptiveGovernor, hardware_governor

__all__ = [
    "HardwareTier",
    "AcceleratorType",
    "HardwareProfile",
    "AdaptiveExecutionPolicy",
    "HardwareAuditor",
    "TierClassifier",
    "TokenBudgeter",
    "DiffusionGovernor",
    "VideoGovernor",
    "MemoryGuard",
    "HardwareMemoryError",
    "AdaptiveGovernor",
    "hardware_governor",
]
