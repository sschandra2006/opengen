"""
Master Engine 5: Motion Graphics Studio.
Orchestrates multimodal footage auditing, direct-response ad directing,
subject-tracking reframing, tri-tier Foley sound design, and headless frame rendering.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union

from opengen.domain.brand import BrandKitSpec
from opengen.engines.motion.models import MotionProjectIR, FootageAuditReport, AdCriticResult
from opengen.engines.motion.ad_director import AdDirectorAgent
from opengen.engines.motion.ad_critic import AdCriticAgent
from opengen.engines.motion.footage_auditor import FootageAuditor
from opengen.engines.motion.smart_reframer import SmartReframer
from opengen.engines.motion.sound_designer import SoundDesigner
from opengen.engines.motion.adapter import MotionSubprocessAdapter

logger = logging.getLogger(__name__)


class MotionEngine:
    """Master generation engine for Engine 5: Motion Graphics Studio."""

    def __init__(self, provider_mgr=None):
        self.provider_mgr = provider_mgr
        self.auditor = FootageAuditor(provider_mgr=provider_mgr)
        self.director = AdDirectorAgent(provider_mgr=provider_mgr)
        self.critic = AdCriticAgent()
        self.reframer = SmartReframer()
        self.sound_designer = SoundDesigner()
        self.adapter = MotionSubprocessAdapter()

    def generate_ad_video(
        self,
        brief: str,
        output_mp4_path: str,
        source_footage: Optional[Union[str, Path]] = None,
        brand: Optional[BrandKitSpec] = None,
        duration: float = 18.0,
        aspect_ratio: str = "9:16",
        voiceover_path: Optional[str] = None,
        music_path: Optional[str] = None,
        auto_correct_violations: bool = True
    ) -> Dict[str, Any]:
        """
        Executes the complete end-to-end Engine 5 generation pipeline:
        1. Saliency footage audit (if footage provided)
        2. 5-Phase direct-response ad planning (<30s)
        3. Pre-flight retention audit & auto-correction
        4. Headless video composition & rendering
        5. Tri-tier Foley audio mastering
        """
        out_mp4 = Path(output_mp4_path).resolve()
        out_mp4.parent.mkdir(parents=True, exist_ok=True)

        # 1. Audit raw footage if supplied
        audit_report: Optional[FootageAuditReport] = None
        if source_footage and Path(source_footage).exists():
            try:
                audit_report = self.auditor.audit_footage(str(source_footage))
                logger.info(f"Source footage audited: {len(audit_report.shots)} micro-shots identified.")
            except Exception as e:
                logger.warning(f"Footage audit skipped due to error: {e}")

        # 2. Plan high-converting ad timeline via AdDirectorAgent
        project_ir = self.director.build_creative_ad_plan(
            brief=brief,
            audit=audit_report,
            brand=brand,
            target_duration=duration,
            target_aspect=aspect_ratio
        )

        # 3. Autonomous Pre-Flight Critic Gate
        audit_result = self.critic.audit_ad_timeline(project_ir)
        if not audit_result["passed"] and auto_correct_violations:
            logger.info("Pre-flight critic flagged violations. Applying automated remediation...")
            project_ir = self.critic.auto_correct_timeline(project_ir, audit_result)
            audit_result = self.critic.audit_ad_timeline(project_ir)

        # 4. Render video frames via Bun/Node headless renderer
        rendered_mp4 = self.adapter.render_project(project_ir, str(out_mp4))

        # 5. Extract SFX cues and master audio track
        sfx_cues = self.sound_designer.extract_sfx_cues_from_project(project_ir)
        if voiceover_path or music_path or sfx_cues:
            mastered_out = str(out_mp4.with_name(f"{out_mp4.stem}_mastered.mp4"))
            final_mp4 = self.sound_designer.master_audio_track(
                video_path=rendered_mp4,
                voiceover_path=voiceover_path,
                music_path=music_path,
                sfx_cues=sfx_cues,
                output_path=mastered_out
            )
            import shutil
            shutil.copy2(final_mp4, str(out_mp4))

        return {
            "file_path": str(out_mp4),
            "duration": project_ir.get("settings", {}).get("duration", duration),
            "aspect_ratio": aspect_ratio,
            "critic_score": audit_result.get("score", 100),
            "critic_violations": audit_result.get("violations", []),
            "project_ir": project_ir
        }

    def reframe_footage(
        self,
        input_video_path: str,
        output_video_path: str,
        focal_override_x: Optional[float] = None
    ) -> str:
        """Dynamically reframes landscape video into 9:16 vertical video using LERP smoothing."""
        return self.reframer.reframe_to_vertical(
            input_video=input_video_path,
            output_video=output_video_path,
            focal_override_x=focal_override_x
        )

    def audit_timeline(self, project_ir: Dict[str, Any]) -> Dict[str, Any]:
        """Audits an ad timeline without rendering."""
        return self.critic.audit_ad_timeline(project_ir)
