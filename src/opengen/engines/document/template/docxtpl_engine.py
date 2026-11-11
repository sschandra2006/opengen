"""
Jinja2 Dynamic Word Templating Engine using docxtpl.
Enables dynamic array loops ({% for item in items %}), conditional sections,
and rich text insertion while preserving native Word styles and table formatting.
"""
import logging
from typing import Dict, Any, Optional
from docxtpl import DocxTemplate
from opengen.engines.document.table_builder import TableBuilder

logger = logging.getLogger(__name__)

class DocxTplEngine:
    """Isolated wrapper for docxtpl Jinja2 dynamic Word template rendering."""

    @classmethod
    def render_template(
        cls,
        template_path: str,
        output_path: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Renders dynamic Jinja2 loops and variables into a DOCX document.
        """
        doc = DocxTemplate(template_path)
        doc.render(context)
        doc.save(output_path)

        # Re-open with python-docx to enforce cantSplit and tblHeader on any expanded dynamic tables
        try:
            import docx
            saved_doc = docx.Document(output_path)
            for table in saved_doc.tables:
                TableBuilder.apply_advanced_properties(table)
            saved_doc.save(output_path)
        except Exception as e:
            logger.warning(f"Could not enforce advanced table properties after Jinja2 render: {e}")

        logger.info(f"Rendered dynamic docxtpl document to {output_path}")
        return output_path
