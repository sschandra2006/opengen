"""
Unified Document Generation Engine (Engine A Coordinator).
Coordinates template preservation, PDF reconstruction, Jinja2 rendering, and visual healing loops.
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from opengen.domain.document import (
    TemplateProfile, MappingReport, FormattingValidationReport
)
from opengen.engines.document.docx_populator import DocxPopulator
from opengen.engines.document.pdf_reconstructor import PdfReconstructor
from opengen.engines.document.template.docxtpl_engine import DocxTplEngine
from opengen.engines.document.validation.auto_corrector import AutoCorrector
from opengen.engines.document.typst_compiler import TypstCompiler
from opengen.domain.brand import BrandKitSpec

logger = logging.getLogger(__name__)

class DocumentEngine:
    """Master entrypoint for Engine A: Document Generation."""

    @classmethod
    def generate_document(
        cls,
        template_path: str,
        output_docx_path: str,
        mapping_report: MappingReport,
        template_profile: TemplateProfile,
        instruction: Optional[str] = None,
        use_jinja2: bool = False,
        jinja2_context: Optional[Dict[str, Any]] = None
    ) -> str:
        ext = Path(template_path).suffix.lower()

        if use_jinja2 and ext == ".docx" and jinja2_context:
            logger.info("Executing Jinja2 dynamic template rendering (docxtpl)")
            return DocxTplEngine.render_template(
                template_path=template_path,
                output_path=output_docx_path,
                context=jinja2_context
            )
        elif ext == ".docx":
            logger.info("Executing DOCX template preservation pipeline")
            return DocxPopulator.populate(
                template_path=template_path,
                output_path=output_docx_path,
                mapping_report=mapping_report,
                template_profile=template_profile,
                instruction=instruction
            )
        elif ext == ".pdf":
            logger.info("Executing PDF template reconstruction pipeline")
            return PdfReconstructor.reconstruct(
                pdf_path=template_path,
                output_docx_path=output_docx_path,
                mapping_report=mapping_report,
                template_profile=template_profile
            )
        else:
            raise ValueError(f"Unsupported template format: '{ext}'. Must be .docx or .pdf")

    @classmethod
    def validate_and_heal(
        cls,
        docx_path: str,
        output_pdf_path: str,
        expected_page_count: int = 1,
        max_iterations: int = 3
    ) -> Tuple[FormattingValidationReport, str]:
        """Runs the 3-loop visual layout healing engine."""
        return AutoCorrector.run_correction_loop(
            docx_path=docx_path,
            pdf_path=output_pdf_path,
            template_page_count=expected_page_count,
            max_iterations=max_iterations
        )

    @classmethod
    def compile_typst(
        cls,
        data: Dict[str, Any],
        output_pdf_path: str,
        brand: Optional[BrandKitSpec] = None
    ) -> str:
        """Compiles high-speed Swiss Editorial PDF with Bento KPI cards via Typst."""
        logger.info(f"Executing Typst high-speed document compilation -> {output_pdf_path}")
        return TypstCompiler.compile_document(
            data=data,
            output_pdf_path=output_pdf_path,
            brand=brand
        )

    @classmethod
    def compile_catalog_typst(
        cls,
        products: List[Dict[str, Any]],
        output_pdf_path: str,
        title: str = "Artisan Product Catalog & Price Guide",
        brand: Optional[BrandKitSpec] = None,
        hero_ratio: float = 0.15
    ) -> str:
        """Compiles an 80/20 Swiss Editorial product catalog with Hero Bento cards and Dot-Leader menus."""
        logger.info(f"Executing Typst retail catalog compilation -> {output_pdf_path}")
        return TypstCompiler.compile_catalog(
            products=products,
            output_pdf_path=output_pdf_path,
            title=title,
            brand=brand,
            hero_ratio=hero_ratio
        )

    @classmethod
    def compile_reference_to_typst_catalog(
        cls,
        reference_pdf_path: str,
        output_pdf_path: str,
        title: Optional[str] = None,
        brand: Optional[BrandKitSpec] = None,
        hero_ratio: float = 0.15
    ) -> str:
        """
        End-to-end pipeline: Extracts tables/products from reference PDF,
        partitions into 80/20 hierarchy, and compiles to Swiss Typst PDF.
        """
        from opengen.engines.document.reference.pymupdf_extractor import PyMuPDFExtractor
        extracted = PyMuPDFExtractor.extract_document(reference_pdf_path)
        tables = extracted.get("tables", [])
        products = []
        for t in tables:
            headers = [h.lower() for h in t.headers]
            for row in t.rows:
                p_entry = {}
                for idx, cell in enumerate(row):
                    if idx < len(headers):
                        h = headers[idx]
                        if any(k in h for k in ["name", "item", "product", "description"]):
                            p_entry["name"] = cell
                        elif any(k in h for k in ["price", "mrp", "rate", "cost"]):
                            p_entry["price"] = cell
                        elif any(k in h for k in ["category", "type", "group"]):
                            p_entry["category"] = cell
                        elif any(k in h for k in ["spec", "weight", "volume", "unit"]):
                            p_entry["spec"] = cell
                    else:
                        p_entry[f"col_{idx}"] = cell
                if p_entry.get("name"):
                    products.append(p_entry)

        # Fallback if no tabular products detected: parse extracted text lines
        if not products:
            text = extracted.get("full_text", "")
            for line in text.split("\n"):
                clean_l = line.strip()
                if " - " in clean_l and len(clean_l) < 80:
                    parts = clean_l.split(" - ")
                    products.append({"name": parts[0].strip(), "price": parts[-1].strip()})
                elif any(curr in clean_l for curr in ["₹", "$", "Rs", "USD", "·"]) and len(clean_l) < 80:
                    parts = clean_l.split()
                    products.append({"name": " ".join(parts[:-1]), "price": parts[-1]})

        doc_title = title or f"{Path(reference_pdf_path).stem.replace('_', ' ').title()} Catalog"
        return cls.compile_catalog_typst(
            products=products,
            output_pdf_path=output_pdf_path,
            title=doc_title,
            brand=brand,
            hero_ratio=hero_ratio
        )
