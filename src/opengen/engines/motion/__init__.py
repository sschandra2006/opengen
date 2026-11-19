"""
Engine 5: Motion Graphics Studio.
AI animated video ads, kinetic typography, 3D scenes, and dynamic reframe engine.
"""
from opengen.engines.motion.engine import MotionEngine
from opengen.engines.motion.adapter import MotionSubprocessAdapter
from opengen.engines.motion.ad_director import AdDirectorAgent
from opengen.engines.motion.ad_critic import AdCriticAgent
from opengen.engines.motion.footage_auditor import FootageAuditor
from opengen.engines.motion.smart_reframer import SmartReframer
from opengen.engines.motion.sound_designer import SoundDesigner
from opengen.engines.motion.templates import MotionTemplateRegistry
from opengen.engines.motion.models import (
    MotionProjectIR,
    FootageAuditReport,
    ScoredMicroShot,
    AdCriticResult,
    FoleyCue
)

__all__ = [
    "MotionEngine",
    "MotionSubprocessAdapter",
    "AdDirectorAgent",
    "AdCriticAgent",
    "FootageAuditor",
    "SmartReframer",
    "SoundDesigner",
    "MotionTemplateRegistry",
    "MotionProjectIR",
    "FootageAuditReport",
    "ScoredMicroShot",
    "AdCriticResult",
    "FoleyCue",
]
