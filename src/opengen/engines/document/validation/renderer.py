"""
Document Renderer for Visual Validation and PDF Export.
Converts generated DOCX into PDF using native Word COM (on Windows)
or headless LibreOffice, with pure Python fallback.
"""
import os
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Optional
import fitz

logger = logging.getLogger(__name__)

class DocumentRenderer:
    """Renders DOCX files to PDF and page images."""

    @classmethod
    def convert_docx_to_pdf(cls, docx_path: str, output_pdf_path: str) -> str:
        docx_abs = str(Path(docx_path).resolve())
        pdf_abs = str(Path(output_pdf_path).resolve())

        # Attempt 1: Native Windows Word COM automation
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
                logger.debug(f"Word COM conversion not available: {e}")
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

        # Fallback: PyMuPDF readable PDF fallback if external office suites are unavailable
        logger.warning("No native Office renderer succeeded; generating fallback PDF structure.")
        cls._create_fallback_pdf(docx_abs, pdf_abs)
        return pdf_abs

    @classmethod
    def _create_fallback_pdf(cls, docx_path: str, pdf_path: str):
        """Creates a readable PDF fallback when neither Word nor LibreOffice is accessible."""
        import docx
        doc = docx.Document(docx_path)
        pdf = fitz.open()
        page = pdf.new_page(width=595, height=842)
        y = 50

        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                page.insert_text((50, y), text[:80], fontsize=10)
                y += 18
                if y > 800:
                    page = pdf.new_page(width=595, height=842)
                    y = 50

        for table in doc.tables:
            for row in table.rows:
                row_str = " | ".join(c.text.strip() for c in row.cells)
                page.insert_text((50, y), row_str[:80], fontsize=9)
                y += 16
                if y > 800:
                    page = pdf.new_page(width=595, height=842)
                    y = 50

        pdf.save(pdf_path)
        pdf.close()
