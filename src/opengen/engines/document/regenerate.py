"""
Document Partial & Section Regeneration Module.
Enables regenerating specific tables or sections without re-running the entire document pipeline.
"""
import logging
from typing import Dict, Any, Optional
import docx

logger = logging.getLogger(__name__)

class DocumentPartialRegenerator:
    """Modifies targeted nodes inside existing DOCX documents."""

    @classmethod
    def regenerate_table(
        cls,
        docx_path: str,
        table_index: int,
        new_rows_data: list,
        output_path: Optional[str] = None
    ) -> str:
        out = output_path or docx_path
        doc = docx.Document(docx_path)

        if table_index <= 0 or table_index > len(doc.tables):
            raise ValueError(f"Table index {table_index} out of range (1 to {len(doc.tables)}).")

        table = doc.tables[table_index - 1]
        # Keep header row (row 0), remove remaining rows
        while len(table.rows) > 1:
            tr = table.rows[-1]._tr
            tr.getparent().remove(tr)

        # Append new rows
        num_cols = len(table.columns)
        for row in new_rows_data:
            new_r = table.add_row()
            for c_i, val in enumerate(row[:num_cols]):
                new_r.cells[c_i].text = str(val)

        doc.save(out)
        logger.info(f"Partially regenerated table {table_index} in {out}")
        return out
