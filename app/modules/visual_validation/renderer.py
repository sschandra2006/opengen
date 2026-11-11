"""
Document Renderer for Module 7: Visual Document Validation.
Converts generated DOCX into PDF using native Word COM on Windows
or headless LibreOffice, and renders PDF pages to PNG for visual inspection.
"""
import os
import subprocess
import shutil
import logging
from pathlib import Path
from typing import List, Optional
import fitz

logger = logging.getLogger(__name__)

class DocumentRenderer:
    """Renders DOCX files to PDF and page images."""

    @classmethod
    def convert_docx_to_pdf(cls, docx_path: str, output_pdf_path: str) -> str:
        docx_abs = str(Path(docx_path).resolve())
        pdf_abs = str(Path(output_pdf_path).resolve())

        # Attempt 1: Native Windows Word COM automation (High-fidelity pixel-perfect output)
        if os.name == "nt":
            word = None
            doc = None
            try:
                import win32com.client
                import pythoncom
                pythoncom.CoInitialize()
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                word.DisplayAlerts = False

                doc = word.Documents.Open(docx_abs)
                # 17 = wdFormatPDF
                doc.SaveAs(pdf_abs, FileFormat=17)
                doc.Close(SaveChanges=False)
                doc = None
                word.Quit()
                word = None

                if Path(pdf_abs).exists() and Path(pdf_abs).stat().st_size > 0:
                    logger.info(f"DOCX successfully converted to PDF via Word COM: {pdf_abs}")
                    return pdf_abs
            except Exception as e:
                logger.warning(f"Word COM conversion failed: {e}")
            finally:
                if doc is not None:
                    try:
                        doc.Close(SaveChanges=False)
                    except Exception:
                        pass
                if word is not None:
                    try:
                        word.Quit()
                    except Exception:
                        pass
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass

        # Attempt 2: Headless LibreOffice
        soffice_cmd = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice_cmd and os.name == "nt":
            for p in [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
            ]:
                if Path(p).exists():
                    soffice_cmd = p
                    break

        if soffice_cmd:
            try:
                out_dir = str(Path(pdf_abs).parent)
                cmd = [soffice_cmd, "--headless", "--convert-to", "pdf", docx_abs, "--outdir", out_dir]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
                produced_pdf = Path(out_dir) / f"{Path(docx_abs).stem}.pdf"
                if produced_pdf.exists():
                    if str(produced_pdf) != pdf_abs:
                        shutil.move(str(produced_pdf), pdf_abs)
                    logger.info(f"DOCX converted to PDF via LibreOffice: {pdf_abs}")
                    return pdf_abs
            except Exception as e:
                logger.warning(f"LibreOffice conversion failed: {e}")

        # Fallback: PyMuPDF / reportlab conversion fallback if external office suites are unavailable
        logger.warning("No native Office renderer succeeded; generating fallback PDF structure.")
        cls._create_fallback_pdf(docx_abs, pdf_abs)
        return pdf_abs

    @classmethod
    def _create_fallback_pdf(cls, docx_path: str, pdf_path: str):
        """Creates a readable PDF fallback when neither Word nor LibreOffice is accessible."""
        import docx
        doc = docx.Document(docx_path)
        pdf_doc = fitz.open()
        page = pdf_doc.new_page(width=595, height=842) # A4
        y = 50
        for p in doc.paragraphs:
            if not p.text.strip():
                continue
            page.insert_text(fitz.Point(50, y), p.text, fontsize=10)
            y += 18
            if y > 780:
                page = pdf_doc.new_page(width=595, height=842)
                y = 50
        pdf_doc.save(pdf_path)
        pdf_doc.close()

    @classmethod
    def render_pdf_to_images(cls, pdf_path: str, output_dir: str) -> List[str]:
        """Renders all PDF pages to PNG images for visual inspection."""
        image_paths = []
        doc = fitz.open(pdf_path)
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        for p_idx, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            img_file = out_path / f"page_{p_idx + 1}.png"
            pix.save(str(img_file))
            image_paths.append(str(img_file))

        doc.close()
        return image_paths
