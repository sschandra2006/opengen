"""
Master Engine 5: Motion Graphics Studio.
Orchestrates multimodal footage auditing, direct-response ad directing,
subject-tracking reframing, tri-tier Foley sound design, and headless frame rendering.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, List

from opengen.domain.brand import BrandKitSpec
from opengen.engines.motion.models import MotionProjectIR, FootageAuditReport, AdCriticResult
from opengen.engines.motion.ad_director import AdDirectorAgent
from opengen.engines.motion.ad_critic import AdCriticAgent
from opengen.engines.motion.footage_auditor import FootageAuditor
from opengen.engines.motion.smart_reframer import SmartReframer
from opengen.engines.motion.sound_designer import SoundDesigner
from opengen.engines.motion.adapter import MotionSubprocessAdapter
from opengen.creative.onetake_cutter import OneTakeCutter
from opengen.creative.collage_broll import CollageBRollGenerator
from opengen.creative.timeline_export import NLETimelineExporter

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
        self.onetake = OneTakeCutter()
        self.collage = CollageBRollGenerator()

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

    def generate_ad_from_folder(
        self,
        folder_path: Union[str, Path],
        output_mp4_path: str,
        brief: Optional[str] = None,
        brand: Optional[BrandKitSpec] = None,
        duration: float = 18.0,
        aspect_ratio: str = "9:16",
        voiceover_path: Optional[str] = None,
        music_path: Optional[str] = None,
        auto_correct_violations: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingests a user folder of video and image assets, audits footage saliency,
        plans a conversion funnel ad, masters Foley audio cues, and exports cleanly
        into the caller's allocated output path.
        """
        f_path = Path(folder_path).resolve()
        if not f_path.exists() or not f_path.is_dir():
            raise FileNotFoundError(f"Content folder does not exist or is not a directory: {folder_path}")

        video_exts = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}
        image_exts = {".jpg", ".jpeg", ".png", ".webp"}

        video_files = sorted([p for p in f_path.iterdir() if p.is_file() and p.suffix.lower() in video_exts])
        image_files = sorted([p for p in f_path.iterdir() if p.is_file() and p.suffix.lower() in image_exts])

        if not video_files and not image_files:
            raise ValueError(f"No video or image assets found in content folder: {folder_path}")

        folder_title = f_path.name.replace("_", " ").replace("-", " ").title()
        effective_brief = brief or f"Direct response commercial presentation for {folder_title} showcasing products and key value propositions."

        # Audit video files for saliency hooks
        audited_shots = []
        best_footage: Optional[Path] = None

        for vid in video_files:
            try:
                report = self.auditor.audit_footage(str(vid))
                if report.shots:
                    for shot in report.shots:
                        audited_shots.append((vid, shot))
            except Exception as e:
                logger.warning(f"Could not audit footage {vid.name}: {e}")

        if audited_shots:
            audited_shots.sort(key=lambda item: item[1].hook_score, reverse=True)
            best_footage = audited_shots[0][0]
        elif video_files:
            best_footage = video_files[0]

        res = self.generate_ad_video(
            brief=effective_brief,
            output_mp4_path=output_mp4_path,
            source_footage=best_footage,
            brand=brand,
            duration=duration,
            aspect_ratio=aspect_ratio,
            voiceover_path=voiceover_path,
            music_path=music_path,
            auto_correct_violations=auto_correct_violations,
        )

        res["folder_path"] = str(f_path)
        res["media_scanned"] = len(video_files) + len(image_files)
        res["video_files_count"] = len(video_files)
        res["image_files_count"] = len(image_files)
        return res

    def audit_timeline(self, project_ir: Dict[str, Any]) -> Dict[str, Any]:
        """Audits an ad timeline without rendering."""
        return self.critic.audit_ad_timeline(project_ir)

    def jump_cut_talking_head(
        self,
        input_video: str,
        output_video: str,
        silence_thresh_sec: float = 0.35,
        zoom_punch_scale: float = 1.25
    ) -> str:
        """Surgically cuts pauses >0.35s and adds alternating camera punch-ins."""
        return self.onetake.process_talking_head(
            input_video=input_video,
            output_video=output_video,
            silence_thresh_sec=silence_thresh_sec,
            zoom_punch_scale=zoom_punch_scale
        )

    def create_bento_mosaic(
        self,
        clips: List[str],
        output_video: str,
        duration: float = 4.0,
        aspect_ratio: str = "9:16"
    ) -> str:
        """Assembles 2 to 4 video feeds into an animated, synchronized Bento Box mosaic."""
        return self.collage.render_bento_mosaic(
            clips=clips,
            output_path=output_video,
            duration=duration,
            aspect_ratio=aspect_ratio
        )

    def export_timeline_edl(
        self,
        project_ir: Dict[str, Any],
        output_edl_path: Optional[str] = None
    ) -> str:
        """Exports project IR scenes into a CMX 3600 EDL for DaVinci Resolve."""
        return NLETimelineExporter.export_cmx3600_edl(
            project_ir=project_ir,
            output_edl_path=output_edl_path
        )

    def export_timeline_fcpxml(
        self,
        project_ir: Dict[str, Any],
        output_fcpxml_path: Optional[str] = None
    ) -> str:
        """Exports project IR scenes into an Apple FCPXML v1.9 timeline."""
        return NLETimelineExporter.export_fcpxml(
            project_ir=project_ir,
            output_fcpxml_path=output_fcpxml_path
        )
