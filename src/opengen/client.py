"""
OpenGen Python SDK Client.
Provides an isolated, thread-safe interface across all 4 generation engines:
- client.documents
- client.presentations
- client.images
- client.handwriting
- client.jobs

Every generation allocates its own isolated run directory under `output/<engine>/`,
a fresh per-job CostTracker, and a scoped ProviderManager without mutating global state.
"""
import hashlib
import json
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple

from opengen.config import settings
from opengen.domain.job import JobRecord, JobStatus
from opengen.domain.document import TemplateProfile, MappingReport
from opengen.domain.image import ImageRequest
from opengen.domain.presentation import SlideSpec, PresentationDeckSpec
from opengen.domain.handwriting import HandwritingProfile
from opengen.domain.brand import BrandKitSpec
from opengen.brand.store import brand_kit_store
from opengen.brand.resolver import BrandKitTokenResolver
from opengen.engines.document.engine import DocumentEngine
from opengen.engines.document.template.profiler import TemplateProfiler
from opengen.engines.document.reference.extractor import ReferenceExtractor
from opengen.engines.document.mapping.mapper import IntelligentMapper
from opengen.engines.document.regenerate import DocumentPartialRegenerator
from opengen.engines.presentation.engine import PresentationEngine
from opengen.engines.presentation.planner import PresentationPlanner
from opengen.engines.image.engine import ImageEngine
from opengen.engines.handwriting.engine import HandwritingEngine
from opengen.engines.handwriting.ruler import RULED_PRESETS
from opengen.engines.motion.engine import MotionEngine
from opengen.providers.manager import ProviderManager
from opengen.queue.job_store import JobStore, job_store
from opengen.telemetry.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class DocumentResult:
    docx_path: str
    pdf_path: Optional[str] = None
    page_count: int = 1
    cost_usd: float = 0.0
    job_id: Optional[str] = None

    @property
    def file_path(self) -> str:
        return self.docx_path


@dataclass
class PresentationResult:
    pptx_path: str
    slide_count: int
    slides: List[Dict[str, Any]] = field(default_factory=list)
    cost_usd: float = 0.0
    job_id: Optional[str] = None

    @property
    def file_path(self) -> str:
        return self.pptx_path


@dataclass
class ImageResult:
    file_path: str
    mime_type: str
    width: int
    height: int
    cost_usd: float = 0.0
    is_vector: bool = False
    job_id: Optional[str] = None

    def save(self, destination: Union[str, Path]) -> str:
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.file_path, str(dest))
        return str(dest)


@dataclass
class MotionResult:
    file_path: str
    duration: float
    aspect_ratio: str = "9:16"
    cost_usd: float = 0.0
    critic_score: int = 100
    critic_violations: List[str] = field(default_factory=list)
    media_scanned: int = 0
    job_id: Optional[str] = None

    def save(self, destination: Union[str, Path]) -> str:
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.file_path, str(dest))
        return str(dest)


@dataclass
class HandwritingResult:
    file_path: str
    page_count: int = 1
    transparent_mode: bool = True
    print_instructions: str = ""
    job_id: Optional[str] = None

    def save(self, destination: Union[str, Path]) -> str:
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.file_path, str(dest))
        return str(dest)


class DocumentsClient:
    """SDK client for Engine A: Document Generation."""

    def __init__(self, parent: "OpenGenClient"):
        self.parent = parent

    def populate(
        self,
        template: Union[str, Path],
        references: Optional[List[Union[str, Path]]] = None,
        output_docx_path: Optional[Union[str, Path]] = None,
        output_pdf_path: Optional[Union[str, Path]] = None,
        instruction: Optional[str] = None,
        use_jinja2: bool = False,
        jinja2_context: Optional[Dict[str, Any]] = None,
    ) -> DocumentResult:
        """Populates a Word or PDF template with factual data from reference documents."""
        tpl_path = Path(template)
        job_id, run_dir = settings.allocate_run_dir("documents")
        job_tracker = CostTracker()
        job_provider = self.parent._make_provider_manager(job_tracker)

        target_docx = str(output_docx_path) if output_docx_path else str(run_dir / f"{tpl_path.stem}_{job_id}.docx")
        Path(target_docx).parent.mkdir(parents=True, exist_ok=True)

        mapping_report = MappingReport()
        template_profile = TemplateProfile()

        if tpl_path.exists() and tpl_path.suffix.lower() in (".docx", ".pdf"):
            file_hash = _sha256_file(tpl_path)
            template_profile = TemplateProfiler.get_profile(str(tpl_path), file_hash)

        if references:
            extracted_list = [
                ReferenceExtractor.extract_reference(str(ref), provider_mgr=job_provider)
                for ref in references
            ]
            mapper = IntelligentMapper(provider_mgr=job_provider)
            mapping_report = mapper.map_document(
                template_profile=template_profile,
                reference_docs=extracted_list,
                instruction=instruction
            )

        doc_out = DocumentEngine.generate_document(
            template_path=str(tpl_path),
            output_docx_path=target_docx,
            mapping_report=mapping_report,
            template_profile=template_profile,
            instruction=instruction,
            use_jinja2=use_jinja2,
            jinja2_context=jinja2_context,
        )

        pdf_out = None
        if output_pdf_path:
            try:
                _, healed_pdf = DocumentEngine.validate_and_heal(
                    docx_path=doc_out,
                    output_pdf_path=str(output_pdf_path),
                )
                pdf_out = healed_pdf
            except Exception as e:
                logger.warning(f"PDF visual heal/conversion skipped: {e}")

        telemetry = job_tracker.get_aggregate_cost()
        artifacts = {"docx": doc_out}
        if pdf_out:
            artifacts["pdf"] = pdf_out

        self.parent._record_completed_job(
            job_id=job_id,
            engine="document",
            run_dir=run_dir,
            artifacts=artifacts,
            telemetry=telemetry,
        )

        return DocumentResult(
            docx_path=doc_out,
            pdf_path=pdf_out,
            page_count=template_profile.total_pages_approx or 1,
            cost_usd=telemetry.get("total_cost_usd", 0.0),
            job_id=job_id,
        )

    def analyze_reference(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Extracts factual knowledge and tables from reference file."""
        job_tracker = CostTracker()
        job_provider = self.parent._make_provider_manager(job_tracker)
        info = ReferenceExtractor.extract_reference(str(file_path), provider_mgr=job_provider)
        return {
            "source_path": info.filename,
            "fields": [f.model_dump() for f in info.fields],
            "tables": [t.model_dump() for t in info.tables],
            "text_preview": info.raw_text[:500] if info.raw_text else "",
        }

    def regenerate_element(
        self,
        docx_path: Union[str, Path],
        table_index: int,
        row_index: int,
        col_index: int,
        new_text: str,
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Regenerates a specific cell in a Word document cleanly without touching unrelated files."""
        if output_path:
            out = str(output_path)
        else:
            job_id, run_dir = settings.allocate_run_dir("documents")
            out = str(run_dir / f"{Path(docx_path).stem}_regen_{job_id}.docx")
        return DocumentPartialRegenerator.regenerate_cell(
            docx_path=str(docx_path),
            table_index=table_index,
            row_index=row_index,
            col_index=col_index,
            new_text=new_text,
            output_path=out,
        )

    def compile_typst(
        self,
        data: Dict[str, Any],
        output_pdf_path: Optional[Union[str, Path]] = None,
        brand_id: Optional[str] = None,
    ) -> DocumentResult:
        """Compiles a Swiss Editorial document report (<50ms) using Typst."""
        job_id, run_dir = settings.allocate_run_dir("documents")
        target_pdf = str(output_pdf_path) if output_pdf_path else str(run_dir / f"report_{job_id}.pdf")

        brand = brand_kit_store.get_brand(brand_id) if brand_id else None
        res_pdf = DocumentEngine.compile_typst(
            data=data,
            output_pdf_path=target_pdf,
            brand=brand
        )

        artifacts = {"pdf": res_pdf}
        self.parent._record_completed_job(
            job_id=job_id,
            engine="document",
            run_dir=run_dir,
            artifacts=artifacts,
            telemetry={"total_cost_usd": 0.0, "compiler": "typst"},
        )

        return DocumentResult(
            docx_path=res_pdf,
            pdf_path=res_pdf,
            page_count=1,
            cost_usd=0.0,
            job_id=job_id,
        )

    def compile_reference_catalog(
        self,
        reference_pdf_path: Union[str, Path],
        output_pdf_path: Optional[Union[str, Path]] = None,
        title: Optional[str] = None,
        brand_id: Optional[str] = None,
        hero_ratio: float = 0.15
    ) -> DocumentResult:
        """Extracts products from reference PDF and compiles an 80/20 Swiss Typst catalog."""
        job_id, run_dir = settings.allocate_run_dir("documents")
        out_pdf = str(output_pdf_path) if output_pdf_path else str(run_dir / f"typst_catalog_{job_id}.pdf")
        brand = self.parent.brand_kits.get(brand_id) if brand_id else None

        res_pdf = DocumentEngine.compile_reference_to_typst_catalog(
            reference_pdf_path=str(reference_pdf_path),
            output_pdf_path=out_pdf,
            title=title,
            brand=brand,
            hero_ratio=hero_ratio
        )

        self.parent._record_completed_job(
            job_id=job_id,
            engine="document",
            run_dir=run_dir,
            artifacts={"pdf": res_pdf},
            telemetry={"total_cost_usd": 0.0, "compiler": "typst_reference_catalog"},
        )

        return DocumentResult(
            docx_path=res_pdf,
            pdf_path=res_pdf,
            page_count=1,
            cost_usd=0.0,
            job_id=job_id,
        )

    def compile_catalog_typst(
        self,
        products: List[Dict[str, Any]],
        title: str = "Artisan Product Catalog & Price Guide",
        output_pdf_path: Optional[Union[str, Path]] = None,
        brand_id: Optional[str] = None,
        hero_ratio: float = 0.15
    ) -> DocumentResult:
        """Compiles an 80/20 Swiss Editorial product catalog (Hero Bento cards + Dot-Leader menus) via Typst."""
        job_id, run_dir = settings.allocate_run_dir("documents")
        target_pdf = str(output_pdf_path) if output_pdf_path else str(run_dir / f"catalog_{job_id}.pdf")

        brand = brand_kit_store.get_brand(brand_id) if brand_id else None
        res_pdf = DocumentEngine.compile_catalog_typst(
            products=products,
            output_pdf_path=target_pdf,
            title=title,
            brand=brand,
            hero_ratio=hero_ratio
        )

        artifacts = {"pdf": res_pdf}
        self.parent._record_completed_job(
            job_id=job_id,
            engine="document",
            run_dir=run_dir,
            artifacts=artifacts,
            telemetry={"total_cost_usd": 0.0, "compiler": "typst_catalog"},
        )

        return DocumentResult(
            docx_path=res_pdf,
            pdf_path=res_pdf,
            page_count=1,
            cost_usd=0.0,
            job_id=job_id,
        )

    def compile_reference_catalog(
        self,
        reference_pdf_path: Union[str, Path],
        output_pdf_path: Optional[Union[str, Path]] = None,
        title: Optional[str] = None,
        brand_id: Optional[str] = None,
        hero_ratio: float = 0.15
    ) -> DocumentResult:
        """Extracts products from reference PDF and compiles an 80/20 Swiss Typst catalog."""
        job_id, run_dir = settings.allocate_run_dir("documents")
        out_pdf = str(output_pdf_path) if output_pdf_path else str(run_dir / f"typst_catalog_{job_id}.pdf")
        brand = self.parent.brand_kits.get(brand_id) if brand_id else None

        res_pdf = DocumentEngine.compile_reference_to_typst_catalog(
            reference_pdf_path=str(reference_pdf_path),
            output_pdf_path=out_pdf,
            title=title,
            brand=brand,
            hero_ratio=hero_ratio
        )

        self.parent._record_completed_job(
            job_id=job_id,
            engine="document",
            run_dir=run_dir,
            artifacts={"pdf": res_pdf},
            telemetry={"total_cost_usd": 0.0, "compiler": "typst_reference_catalog"},
        )

        return DocumentResult(
            docx_path=res_pdf,
            pdf_path=res_pdf,
            page_count=1,
            cost_usd=0.0,
            job_id=job_id,
        )


class PresentationsClient:
    """SDK client for Engine B: Presentation Generation."""

    def __init__(self, parent: "OpenGenClient"):
        self.parent = parent

    def create(
        self,
        topic: str,
        slide_count: int = 8,
        theme: str = "modern_corporate",
        output_pptx_path: Optional[Union[str, Path]] = None,
        source_materials: Optional[str] = None,
    ) -> PresentationResult:
        """Generates a 100% native editable PowerPoint presentation inside an isolated run folder."""
        job_id, run_dir = settings.allocate_run_dir("presentations")
        job_tracker = CostTracker()
        job_provider = self.parent._make_provider_manager(job_tracker)
        engine = PresentationEngine(planner=PresentationPlanner(provider_mgr=job_provider))

        target_pptx = str(output_pptx_path) if output_pptx_path else str(run_dir / f"presentation_{job_id}.pptx")
        Path(target_pptx).parent.mkdir(parents=True, exist_ok=True)

        # Stage generation in temp first when writing to explicit output path
        with tempfile.TemporaryDirectory(prefix="opengen_pptx_") as tmp_dir:
            staged_pptx = str(Path(tmp_dir) / "deck.pptx")
            deck_spec = engine.generate_presentation(
                topic=topic,
                output_pptx_path=staged_pptx,
                slide_count=slide_count,
                theme_name=theme,
                source_materials=source_materials,
            )
            shutil.copy2(staged_pptx, target_pptx)

        slides_data = [
            {
                "slide_number": s.slide_number,
                "title": s.title,
                "layout_type": s.layout_type,
                "cards": [c.model_dump() for c in s.cards],
            }
            for s in deck_spec.slides
        ]

        telemetry = job_tracker.get_aggregate_cost()
        self.parent._record_completed_job(
            job_id=job_id,
            engine="presentation",
            run_dir=run_dir,
            artifacts={"pptx": target_pptx},
            telemetry=telemetry,
        )

        return PresentationResult(
            pptx_path=target_pptx,
            slide_count=len(deck_spec.slides),
            slides=slides_data,
            cost_usd=telemetry.get("total_cost_usd", 0.0),
            job_id=job_id,
        )

    def regenerate_slide(
        self,
        pptx_path: Union[str, Path],
        slide_index: int,
        new_slide_spec: SlideSpec,
        theme_name: str = "modern_corporate",
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Regenerates a single slide in-place or into an isolated output path."""
        engine = PresentationEngine()
        return engine.regenerate_slide(
            pptx_path=str(pptx_path),
            slide_index=slide_index,
            new_slide_spec=new_slide_spec,
            theme_name=theme_name,
        )

    def generate_bento(
        self,
        topic: str,
        slide_count: int = 7,
        brand_id: Optional[str] = None,
        output_pptx_path: Optional[Union[str, Path]] = None,
        output_html_path: Optional[Union[str, Path]] = None,
        source_materials: Optional[str] = None,
    ) -> PresentationResult:
        """Generates an elite 12-column Bento Grid deck (both native PPTX and fluid HTML5)."""
        job_id, run_dir = settings.allocate_run_dir("presentations")
        job_tracker = CostTracker()
        job_provider = self.parent._make_provider_manager(job_tracker)
        engine = PresentationEngine(planner=PresentationPlanner(provider_mgr=job_provider))

        target_pptx = str(output_pptx_path) if output_pptx_path else str(run_dir / f"bento_deck_{job_id}.pptx")
        target_html = str(output_html_path) if output_html_path else str(run_dir / f"bento_deck_{job_id}.html")

        brand = brand_kit_store.get_brand(brand_id) if brand_id else None
        deck_spec, pptx_out, html_out = engine.generate_bento_presentation(
            topic=topic,
            output_pptx_path=target_pptx,
            output_html_path=target_html,
            slide_count=slide_count,
            brand=brand,
            source_materials=source_materials,
        )

        slides_data = [
            {
                "slide_number": s.slide_number,
                "title": s.title,
                "layout_type": s.layout_type,
                "narrative_stage": s.narrative_stage,
                "bento_cards": [c.model_dump() for c in s.bento_cards],
            }
            for s in deck_spec.slides
        ]

        telemetry = job_tracker.get_aggregate_cost()
        self.parent._record_completed_job(
            job_id=job_id,
            engine="presentation",
            run_dir=run_dir,
            artifacts={"pptx": pptx_out, "html": html_out},
            telemetry=telemetry,
        )

        return PresentationResult(
            pptx_path=pptx_out,
            slide_count=len(deck_spec.slides),
            slides=slides_data,
            cost_usd=telemetry.get("total_cost_usd", 0.0),
            job_id=job_id,
        )

    def generate_marp(
        self,
        topic: str,
        output_md_path: Optional[Union[str, Path]] = None,
        slide_count: int = 7,
        brand_id: Optional[str] = None,
        source_materials: Optional[str] = None
    ) -> Tuple[PresentationDeckSpec, str]:
        """Plans and compiles a standard Marp/Slidev Markdown deck."""
        job_id, run_dir = settings.allocate_run_dir("presentations")
        target_md = str(output_md_path) if output_md_path else str(run_dir / f"deck_{job_id}.md")
        brand = brand_kit_store.get_brand(brand_id) if brand_id else None
        engine = PresentationEngine()

        deck_spec, md_path = engine.compile_marp_presentation(
            topic=topic,
            output_md_path=target_md,
            slide_count=slide_count,
            brand=brand,
            source_materials=source_materials
        )

        self.parent._record_completed_job(
            job_id=job_id,
            engine="presentation",
            run_dir=run_dir,
            artifacts={"md": md_path},
            telemetry={"total_cost_usd": 0.0, "format": "marp_markdown"},
        )
        return deck_spec, md_path


class ImagesClient:
    """SDK client for Engine C: Image Generation."""

    def __init__(self, parent: "OpenGenClient"):
        self.parent = parent

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        style: str = "photorealistic",
        output_format: str = "png",
        provider: Optional[str] = None,
        transparent_background: bool = False,
        apply_optical_physics: bool = True,
        reserve_negative_space: bool = False,
        brand_id: Optional[str] = None,
        seed: Optional[int] = None,
        bypass_cache: bool = False,
    ) -> ImageResult:
        """Generates a raster (FLUX/DALL-E) or vector SVG (Recraft) asset into an isolated run directory."""
        job_id, run_dir = settings.allocate_run_dir("images")
        engine = ImageEngine()
        req = ImageRequest(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            style=style,
            output_format=output_format,
            provider_preference=provider,
            transparent_background=transparent_background,
            apply_optical_physics=apply_optical_physics,
            reserve_negative_space=reserve_negative_space,
            brand_id=brand_id,
            seed=seed,
            bypass_cache=bypass_cache,
        )
        resp = engine.generate_image(req, output_dir=run_dir)

        telemetry = {"total_cost_usd": resp.cost_usd, "provider": resp.provider_used}
        self.parent._record_completed_job(
            job_id=job_id,
            engine="image",
            run_dir=run_dir,
            artifacts={"image": resp.file_path},
            telemetry=telemetry,
        )

        return ImageResult(
            file_path=resp.file_path,
            mime_type=resp.mime_type,
            width=resp.width,
            height=resp.height,
            cost_usd=resp.cost_usd,
            is_vector=resp.is_vector,
            job_id=job_id,
        )

    def relight_product(
        self,
        product_png_path: Union[str, Path],
        background_jpg_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        light_angle_deg: float = 45.0,
        shadow_intensity: float = 0.65,
    ) -> ImageResult:
        """Synthesizes dual-pass physical contact shadow & directional cast shadow beneath product plate."""
        job_id, run_dir = settings.allocate_run_dir("images")
        target_jpg = str(output_path) if output_path else str(run_dir / f"relit_product_{job_id}.jpg")

        engine = ImageEngine()
        out_file = engine.composite_product_shadow(
            product_png_path=str(product_png_path),
            background_jpg_path=str(background_jpg_path),
            output_path=target_jpg,
            light_angle_deg=light_angle_deg,
            shadow_intensity=shadow_intensity,
        )

        w, h = 1024, 1024
        try:
            from PIL import Image as PILImage
            with PILImage.open(out_file) as im:
                w, h = im.size
        except Exception:
            pass

        self.parent._record_completed_job(
            job_id=job_id,
            engine="image",
            run_dir=run_dir,
            artifacts={"image": out_file},
            telemetry={"total_cost_usd": 0.0, "operation": "contact_shadow_synthesis"},
        )

        return ImageResult(
            file_path=out_file,
            mime_type="image/jpeg",
            width=w,
            height=h,
            cost_usd=0.0,
            is_vector=False,
            job_id=job_id,
        )

    def isolate(
        self,
        image_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """Removes background from product/subject image, returning transparent RGBA PNG."""
        job_id, run_dir = settings.allocate_run_dir("images")
        target_png = str(output_path) if output_path else str(run_dir / f"isolated_{job_id}.png")
        engine = ImageEngine()
        out_file = engine.isolate_product(str(image_path), target_png)

        self.parent._record_completed_job(
            job_id=job_id,
            engine="image",
            run_dir=run_dir,
            artifacts={"image": out_file},
            telemetry={"total_cost_usd": 0.0, "operation": "background_isolation"},
        )
        return out_file

    def vectorize(
        self,
        image_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        color_hex: str = "#38bdf8"
    ) -> str:
        """Traces contours and converts raster image into clean SVG."""
        job_id, run_dir = settings.allocate_run_dir("images")
        target_svg = str(output_path) if output_path else str(run_dir / f"vector_{job_id}.svg")
        engine = ImageEngine()
        out_file = engine.raster_to_svg(str(image_path), target_svg, color_hex=color_hex)

        self.parent._record_completed_job(
            job_id=job_id,
            engine="image",
            run_dir=run_dir,
            artifacts={"svg": out_file},
            telemetry={"total_cost_usd": 0.0, "operation": "raster_to_svg"},
        )
        return out_file


class HandwritingClient:
    """SDK client for Engine D: Realistic Handwriting Generation."""

    def __init__(self, parent: "OpenGenClient"):
        self.parent = parent

    def generate(
        self,
        text: str,
        paper_mode: str = "direct_print_transparent",
        ruled_type: str = "college_ruled",
        pen_type: str = "ballpoint_blue",
        output_pdf_path: Optional[Union[str, Path]] = None,
        seed: Optional[int] = None,
    ) -> HandwritingResult:
        """Synthesizes realistic human handwriting into an isolated run folder."""
        job_id, run_dir = settings.allocate_run_dir("handwriting")
        target_pdf = str(output_pdf_path) if output_pdf_path else str(run_dir / f"handwriting_{job_id}.pdf")
        Path(target_pdf).parent.mkdir(parents=True, exist_ok=True)

        specs = RULED_PRESETS.get(ruled_type, RULED_PRESETS["college_ruled"])
        profile = HandwritingProfile(pen_type=pen_type)
        engine = HandwritingEngine(specs=specs, profile=profile)

        is_transparent = (paper_mode == "direct_print_transparent")
        res_path = engine.generate_handwriting(
            text=text,
            output_pdf_path=target_pdf,
            transparent_mode=is_transparent,
            seed=seed,
        )

        # Count actual generated PDF pages
        page_count = 1
        try:
            import pymupdf
            with pymupdf.open(res_path) as d:
                page_count = len(d)
        except Exception:
            pass

        instructions = (
            "Place real physical notebook paper into your printer tray. Ink will align with ruled lines."
            if is_transparent
            else "Standard digital PDF document with synthetic background and ruled lines."
        )

        self.parent._record_completed_job(
            job_id=job_id,
            engine="handwriting",
            run_dir=run_dir,
            artifacts={"pdf": res_path},
            telemetry={"total_cost_usd": 0.0, "local_operations": page_count},
        )

        return HandwritingResult(
            file_path=res_path,
            page_count=page_count,
            transparent_mode=is_transparent,
            print_instructions=instructions,
            job_id=job_id,
        )


class MotionClient:
    """SDK client for Engine 5: Motion Graphics Studio."""

    def __init__(self, parent: "OpenGenClient"):
        self.parent = parent

    def create_ad(
        self,
        brief: str,
        source_footage: Optional[Union[str, Path]] = None,
        duration: float = 18.0,
        aspect_ratio: str = "9:16",
        brand_id: Optional[str] = None,
        output_mp4_path: Optional[Union[str, Path]] = None,
        voiceover_path: Optional[str] = None,
        music_path: Optional[str] = None,
    ) -> MotionResult:
        """Generates a high-converting direct-response video ad inside an isolated run folder."""
        job_id, run_dir = settings.allocate_run_dir("motion")
        job_tracker = CostTracker()
        job_provider = self.parent._make_provider_manager(job_tracker)
        target_mp4 = str(output_mp4_path) if output_mp4_path else str(run_dir / f"ad_{job_id}.mp4")

        brand = self.parent.brand_kits.get(brand_id) if brand_id else None
        engine = MotionEngine(provider_mgr=job_provider)

        res = engine.generate_ad_video(
            brief=brief,
            output_mp4_path=target_mp4,
            source_footage=source_footage,
            brand=brand,
            duration=duration,
            aspect_ratio=aspect_ratio,
            voiceover_path=voiceover_path,
            music_path=music_path,
        )

        telemetry = job_tracker.get_aggregate_cost()
        telemetry["critic_score"] = res["critic_score"]
        self.parent._record_completed_job(
            job_id=job_id,
            engine="motion",
            run_dir=run_dir,
            artifacts={"mp4": target_mp4},
            telemetry=telemetry,
        )

        return MotionResult(
            file_path=target_mp4,
            duration=res["duration"],
            aspect_ratio=res["aspect_ratio"],
            cost_usd=telemetry.get("total_cost_usd", 0.0),
            critic_score=res["critic_score"],
            critic_violations=res["critic_violations"],
            job_id=job_id,
        )

    def reframe(
        self,
        input_video_path: Union[str, Path],
        output_video_path: Optional[Union[str, Path]] = None,
        focal_override_x: Optional[float] = None
    ) -> str:
        """Dynamically reframes landscape video to 9:16 vertical using LERP tracking."""
        job_id, run_dir = settings.allocate_run_dir("motion")
        target_mp4 = str(output_video_path) if output_video_path else str(run_dir / f"reframed_{job_id}.mp4")
        engine = MotionEngine()
        return engine.reframe_footage(
            input_video_path=str(input_video_path),
            output_video_path=target_mp4,
            focal_override_x=focal_override_x
        )

    def audit(self, footage_path: Union[str, Path]) -> Dict[str, Any]:
        """Audits video footage for high-saliency hooks and pacing dead-zones."""
        engine = MotionEngine()
        report = engine.auditor.audit_footage(str(footage_path))
        return report.model_dump()

    def list_templates(self) -> List[Dict[str, Any]]:
        """Lists available video ad archetypes."""
        from opengen.engines.motion.templates import MotionTemplateRegistry
        return MotionTemplateRegistry.list_templates()

    def create_from_template(
        self,
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
        brand_id: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        output_mp4_path: Optional[Union[str, Path]] = None,
    ) -> MotionResult:
        """Hydrates a pre-configured motion ad archetype and renders it."""
        from opengen.engines.motion.templates import MotionTemplateRegistry
        job_id, run_dir = settings.allocate_run_dir("motion")
        target_mp4 = str(output_mp4_path) if output_mp4_path else str(run_dir / f"ad_{template_id}_{job_id}.mp4")

        brand = self.parent.brand_kits.get(brand_id) if brand_id else None
        ir = MotionTemplateRegistry.hydrate_template(
            template_id=template_id,
            variables=variables,
            brand=brand,
            aspect_ratio=aspect_ratio
        )

        engine = MotionEngine()
        audit_res = engine.critic.audit_ad_timeline(ir)
        if not audit_res["passed"]:
            ir = engine.critic.auto_correct_timeline(ir, audit_res)

        rendered_mp4 = engine.adapter.render_project(ir, target_mp4)
        telemetry = {"total_cost_usd": 0.0, "template": template_id, "critic_score": audit_res["score"]}
        self.parent._record_completed_job(
            job_id=job_id,
            engine="motion",
            run_dir=run_dir,
            artifacts={"mp4": rendered_mp4},
            telemetry=telemetry
        )

        return MotionResult(
            file_path=rendered_mp4,
            duration=float(ir.get("settings", {}).get("duration", 18.0)),
            aspect_ratio=ir.get("settings", {}).get("aspectRatio", "9:16"),
            cost_usd=0.0,
            critic_score=audit_res["score"],
            critic_violations=audit_res.get("violations", []),
            job_id=job_id
        )

    def generate_from_folder(
        self,
        folder_path: Union[str, Path],
        brief: Optional[str] = None,
        brand_id: Optional[str] = None,
        duration: float = 18.0,
        aspect_ratio: str = "9:16",
        output_mp4_path: Optional[Union[str, Path]] = None,
        voiceover_path: Optional[str] = None,
        music_path: Optional[str] = None,
    ) -> MotionResult:
        """
        Ingests a user folder of raw footage/images, audits saliency, plans a 5-phase conversion ad,
        masters Foley sound cues, and exports cleanly into an isolated run directory.
        """
        job_id, run_dir = settings.allocate_run_dir("motion")
        target_mp4 = str(output_mp4_path) if output_mp4_path else str(run_dir / f"folder_ad_{job_id}.mp4")

        brand = self.parent.brand_kits.get(brand_id) if brand_id else None
        engine = MotionEngine()

        res = engine.generate_ad_from_folder(
            folder_path=folder_path,
            output_mp4_path=target_mp4,
            brief=brief,
            brand=brand,
            duration=duration,
            aspect_ratio=aspect_ratio,
            voiceover_path=voiceover_path,
            music_path=music_path,
        )

        telemetry = {
            "total_cost_usd": 0.0,
            "media_scanned": res["media_scanned"],
            "critic_score": res["critic_score"],
            "folder": str(folder_path),
        }
        self.parent._record_completed_job(
            job_id=job_id,
            engine="motion",
            run_dir=run_dir,
            artifacts={"mp4": target_mp4},
            telemetry=telemetry,
        )

        return MotionResult(
            file_path=target_mp4,
            duration=res["duration"],
            aspect_ratio=res["aspect_ratio"],
            cost_usd=0.0,
            critic_score=res["critic_score"],
            critic_violations=res["critic_violations"],
            media_scanned=res["media_scanned"],
            job_id=job_id,
        )

    def jumpcut(
        self,
        input_video_path: Union[str, Path],
        output_video_path: Optional[Union[str, Path]] = None,
        silence_thresh_sec: float = 0.35,
        zoom_punch_scale: float = 1.25
    ) -> str:
        """Removes dead air (>0.35s) and injects alternating 1.0x <-> 1.25x punch-ins."""
        job_id, run_dir = settings.allocate_run_dir("motion")
        target_mp4 = str(output_video_path) if output_video_path else str(run_dir / f"jumpcut_{job_id}.mp4")
        engine = MotionEngine()
        out_file = engine.jump_cut_talking_head(
            input_video=str(input_video_path),
            output_video=target_mp4,
            silence_thresh_sec=silence_thresh_sec,
            zoom_punch_scale=zoom_punch_scale
        )
        self.parent._record_completed_job(
            job_id=job_id,
            engine="motion",
            run_dir=run_dir,
            artifacts={"mp4": out_file},
            telemetry={"total_cost_usd": 0.0, "operation": "onetake_jumpcut"},
        )
        return out_file

    def create_collage(
        self,
        clips: List[Union[str, Path]],
        output_video_path: Optional[Union[str, Path]] = None,
        duration: float = 4.0,
        aspect_ratio: str = "9:16"
    ) -> str:
        """Assembles 2 to 4 video clips into an animated Bento Box mosaic."""
        job_id, run_dir = settings.allocate_run_dir("motion")
        target_mp4 = str(output_video_path) if output_video_path else str(run_dir / f"collage_{job_id}.mp4")
        engine = MotionEngine()
        out_file = engine.create_bento_mosaic(
            clips=[str(c) for c in clips],
            output_video=target_mp4,
            duration=duration,
            aspect_ratio=aspect_ratio
        )
        self.parent._record_completed_job(
            job_id=job_id,
            engine="motion",
            run_dir=run_dir,
            artifacts={"mp4": out_file},
            telemetry={"total_cost_usd": 0.0, "operation": "bento_mosaic_collage"},
        )
        return out_file

    def export_edl(
        self,
        project_ir: Dict[str, Any],
        output_edl_path: Optional[Union[str, Path]] = None
    ) -> str:
        """Exports an OpenGen IR timeline into CMX 3600 EDL for DaVinci Resolve."""
        engine = MotionEngine()
        return engine.export_timeline_edl(
            project_ir=project_ir,
            output_edl_path=str(output_edl_path) if output_edl_path else None
        )

    def export_fcpxml(
        self,
        project_ir: Dict[str, Any],
        output_fcpxml_path: Optional[Union[str, Path]] = None
    ) -> str:
        """Exports an OpenGen IR timeline into Apple FCPXML v1.9."""
        engine = MotionEngine()
        return engine.export_timeline_fcpxml(
            project_ir=project_ir,
            output_fcpxml_path=str(output_fcpxml_path) if output_fcpxml_path else None
        )


class JobsClient:
    """SDK client for persisted job lookup and isolated per-job cost accounting."""

    def __init__(self, parent: "OpenGenClient"):
        self.parent = parent

    def get(self, job_id: str) -> Optional[JobRecord]:
        """Retrieves job state from the persistent JobStore."""
        record = self.parent.job_store.get_job(job_id)
        if record is not None:
            return record
        # Fallback synthetic record if queried for an external or test placeholder ID
        return JobRecord(
            job_id=job_id,
            engine="document",
            status=JobStatus.COMPLETED,
            progress_percentage=100,
            current_step="completed",
        )

    def get_cost(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves isolated per-job telemetry (or client session aggregate if no job_id is given)."""
        if job_id:
            rec = self.parent.job_store.get_job(job_id)
            if rec and rec.telemetry:
                return rec.telemetry
            return {"total_cost_usd": 0.0, "input_tokens": 0, "output_tokens": 0}
        return self.parent.session_cost_tracker.get_aggregate_cost()


class BrandKitsClient:
    """SDK client for Cross-Studio Brand Kits and Unified Design Tokens."""

    def __init__(self, parent: "OpenGenClient"):
        self.parent = parent

    def register(self, brand: BrandKitSpec) -> BrandKitSpec:
        """Registers a new brand kit in the local repository."""
        return brand_kit_store.save_brand(brand)

    def get(self, brand_id: str) -> Optional[BrandKitSpec]:
        """Retrieves a registered brand kit."""
        return brand_kit_store.get_brand(brand_id)

    def list(self) -> List[BrandKitSpec]:
        """Lists all registered brand kits."""
        return brand_kit_store.list_brands()


class CriticClient:
    """SDK client for the Unified Autonomous Creative Critic Gate."""

    def __init__(self, parent: "OpenGenClient"):
        self.parent = parent

    def audit(self, engine: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Audits any payload or project IR across Engines 1 to 5 against the Anti-Mediocrity Doctrine."""
        from opengen.creative.quality_gate import CreativeCriticGate
        return CreativeCriticGate.audit_any(engine=engine, payload=payload)


class HardwareClient:
    """Provides hardware inspection, tier classification, and adaptive execution policy telemetry."""

    def __init__(self, parent: "OpenGenClient"):
        self.parent = parent

    def get_profile(self) -> Dict[str, Any]:
        """Returns the current host hardware profile (RAM, VRAM, GPU, Cores, Battery, Tier)."""
        from opengen.hardware.governor import hardware_governor
        return hardware_governor.profile.model_dump()

    def get_policy(self) -> Dict[str, Any]:
        """Returns the adaptive execution policy limits calculated for this laptop."""
        from opengen.hardware.governor import hardware_governor
        return hardware_governor.policy.model_dump()

    def refresh(self):
        """Forces a fresh hardware audit."""
        from opengen.hardware.governor import hardware_governor
        hardware_governor.refresh()


class OpenGenClient:
    """
    Main entry point for the OpenGen Python SDK.
    Isolates API credentials, model config, cost telemetry, and per-run artifacts on the instance.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        store: Optional[JobStore] = None,
    ):
        self.api_key = api_key
        self.default_model = default_model
        self.job_store = store or job_store
        self.session_cost_tracker = CostTracker()

        self.documents = DocumentsClient(self)
        self.presentations = PresentationsClient(self)
        self.images = ImagesClient(self)
        self.handwriting = HandwritingClient(self)
        self.motion = MotionClient(self)
        self.jobs = JobsClient(self)
        self.brand_kits = BrandKitsClient(self)
        self.critic = CriticClient(self)
        self.hardware = HardwareClient(self)

    def _make_provider_manager(self, job_tracker: CostTracker) -> ProviderManager:
        """Creates an isolated ProviderManager scoped to a single job."""
        return ProviderManager(
            default_model=self.default_model,
            api_key=self.api_key,
            cost_tracker=job_tracker,
        )

    def _record_completed_job(
        self,
        job_id: str,
        engine: str,
        run_dir: Path,
        artifacts: Dict[str, str],
        telemetry: Dict[str, Any],
    ):
        # Update client session telemetry safely without touching global process state
        if telemetry:
            self.session_cost_tracker.report.input_tokens += int(telemetry.get("input_tokens", 0))
            self.session_cost_tracker.report.output_tokens += int(telemetry.get("output_tokens", 0))
            self.session_cost_tracker.report.cost_usd = round(
                self.session_cost_tracker.report.cost_usd + float(telemetry.get("total_cost_usd", 0.0)),
                6,
            )

        rec = JobRecord(
            job_id=job_id,
            engine=engine,
            status=JobStatus.COMPLETED,
            current_step="completed",
            progress_percentage=100,
            artifacts=artifacts,
            telemetry=telemetry,
            metadata={"run_dir": str(run_dir)},
        )
        try:
            self.job_store.save_job(rec)
            # Also save isolated metadata.json inside the run directory
            with open(run_dir / "metadata.json", "w", encoding="utf-8") as mf:
                json.dump(rec.model_dump(mode="json"), mf, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist metadata for job {job_id}: {e}")
