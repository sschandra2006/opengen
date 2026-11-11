"""
Master End-to-End Orchestrator Pipeline.
Coordinates all modules: validation, profiling, extraction, mapping,
generation, visual validation, token tracking, and persistent caching.
"""
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import settings
from app.models.api_schemas import DocumentJobStatus
from app.models.template_profile import TemplateProfile
from app.models.extracted_info import ExtractedInformation
from app.models.mapping import MappingReport
from app.models.validation_report import FormattingValidationReport
from app.modules.memory_cache.storage import storage
from app.modules.token_optimization.tracker import TokenTracker
from app.modules.token_optimization.ai_router import AIRouter
from app.modules.template_intelligence.profiler import TemplateProfiler
from app.modules.reference_intelligence.information_extractor import ReferenceIntelligenceEngine
from app.modules.intelligent_mapping.mapper import IntelligentMapper
from app.modules.document_generation.generator import DocumentGenerator
from app.modules.visual_validation.auto_corrector import AutoCorrector

logger = logging.getLogger(__name__)

class DocumentGenerationPipeline:
    """Executes the complete document generation workflow."""

    def __init__(self):
        self.tracker = TokenTracker()
        self.ai_router = AIRouter(self.tracker)
        self.ref_engine = ReferenceIntelligenceEngine(self.ai_router)
        self.mapper = IntelligentMapper(self.ai_router)

    def run(
        self,
        job_id: str,
        template_file_id: str,
        reference_file_ids: List[str],
        additional_text: Optional[str] = None,
        instruction: Optional[str] = None,
        output_format: str = "docx",
        user_clarifications: Optional[Dict[str, Any]] = None
    ) -> DocumentJobStatus:
        logger.info(f"Starting document pipeline for job {job_id}")

        def update_progress(step: str, percentage: int, extra_data: Optional[Dict[str, Any]] = None):
            data = extra_data or {}
            storage.save_job(job_id, status=step, current_step=step, progress=percentage, data=data)

        try:
            # Stage 1: Input Resolution
            update_progress("analysing_template", 10)
            templ_file = storage.get_file_by_id(template_file_id)
            if not templ_file:
                raise ValueError(f"Template file '{template_file_id}' not found.")

            templ_path = templ_file["storage_path"]
            templ_hash = templ_file["sha256"]

            # Stage 2: Template Profiling (cached if seen before)
            template_profile = TemplateProfiler.get_profile(templ_path, templ_hash)
            self.tracker.record_local_op(1)

            # Stage 3: Reading Reference Documents
            update_progress("reading_references", 25)
            ref_docs: List[ExtractedInformation] = []
            for r_id in reference_file_ids:
                r_file = storage.get_file_by_id(r_id)
                if r_file:
                    ref_info = self.ref_engine.process_reference(r_file["storage_path"], r_file["sha256"])
                    ref_docs.append(ref_info)
                    self.tracker.record_local_op(1)

            # Stage 4: Information Extraction & Semantic Mapping
            update_progress("mapping_info", 45)
            mapping_report = self.mapper.map_document(
                template_profile=template_profile,
                reference_docs=ref_docs,
                additional_text=additional_text,
                instruction=instruction,
                user_clarifications=user_clarifications
            )

            # Check if user clarification is strictly required
            if mapping_report.requires_user_clarification and not user_clarifications:
                logger.info(f"Job {job_id} requires user clarification.")
                clarification_data = {
                    "template_profile": template_profile.model_dump(),
                    "mapping_report": mapping_report.model_dump(),
                    "clarifications_needed": mapping_report.clarification_questions
                }
                update_progress("pending_clarification", 50, clarification_data)
                return DocumentJobStatus(
                    job_id=job_id,
                    status="pending_clarification",
                    progress_percentage=50,
                    current_step="pending_clarification",
                    template_profile=template_profile.model_dump(),
                    mapping_report=mapping_report.model_dump(),
                    clarifications_needed=mapping_report.clarification_questions
                )

            # Stage 5: Document Generation
            update_progress("generating_docx", 65)
            gen_dir = settings.HISTORY_DIR / job_id
            gen_dir.mkdir(parents=True, exist_ok=True)

            out_docx = gen_dir / f"generated_{Path(templ_file['filename']).stem}.docx"
            out_pdf = gen_dir / f"generated_{Path(templ_file['filename']).stem}.pdf"

            generated_docx_path = DocumentGenerator.generate(
                template_path=templ_path,
                output_docx_path=str(out_docx),
                mapping_report=mapping_report,
                template_profile=template_profile,
                instruction=instruction
            )
            self.tracker.record_local_op(1)

            # Stage 6: Visual Validation & Auto-Correction
            update_progress("checking_formatting", 85)
            validation_report, final_pdf_path = AutoCorrector.run_correction_loop(
                docx_path=generated_docx_path,
                pdf_path=str(out_pdf),
                template_page_count=template_profile.total_pages_approx,
                max_iterations=settings.MAX_VALIDATION_ATTEMPTS
            )
            self.tracker.record_local_op(1)

            # Stage 7: Finalizing & Reporting
            update_progress("completed", 100)
            token_summary = self.tracker.get_summary()

            # Save full job result artifacts in history
            final_job_data = {
                "template_profile": template_profile.model_dump(),
                "extracted_data": [d.model_dump() for d in ref_docs],
                "mapping_report": mapping_report.model_dump(),
                "validation_report": validation_report.model_dump(),
                "token_usage": token_summary,
                "docx_path": str(out_docx),
                "pdf_path": str(final_pdf_path),
                "docx_download_url": f"/api/download/{job_id}/docx",
                "pdf_download_url": f"/api/download/{job_id}/pdf"
            }
            update_progress("completed", 100, final_job_data)

            return DocumentJobStatus(
                job_id=job_id,
                status="completed",
                progress_percentage=100,
                current_step="completed",
                template_profile=template_profile.model_dump(),
                extracted_data=[d.model_dump() for d in ref_docs],
                mapping_report=mapping_report.model_dump(),
                validation_report=validation_report.model_dump(),
                token_usage=token_summary,
                docx_download_url=f"/api/download/{job_id}/docx",
                pdf_download_url=f"/api/download/{job_id}/pdf"
            )

        except Exception as e:
            logger.exception(f"Pipeline failure for job {job_id}: {e}")
            error_msg = str(e)
            storage.save_job(job_id, status="failed", current_step="failed", progress=0, data={"error": error_msg})
            return DocumentJobStatus(
                job_id=job_id,
                status="failed",
                progress_percentage=0,
                current_step="failed",
                error_message=error_msg
            )
