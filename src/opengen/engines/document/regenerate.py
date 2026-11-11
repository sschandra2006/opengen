"""
Document Partial & Section Regeneration Module.
Enables regenerating specific tables or cells without re-running the entire document pipeline.
"""
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import docx

logger = logging.getLogger(__name__)


class DocumentPartialRegenerator:
    """Modifies targeted nodes inside existing DOCX documents safely via temp staging."""

    @classmethod
    def regenerate_table(
        cls,
        docx_path: str,
        table_index: int,
        new_rows_data: list,
        output_path: Optional[str] = None
    ) -> str:
        out = Path(output_path or docx_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="opengen_regen_") as tmp_dir:
            staged = Path(tmp_dir) / "staged.docx"
            shutil.copy2(docx_path, staged)
            doc = docx.Document(str(staged))

            if table_index <= 0 or table_index > len(doc.tables):
                raise ValueError(f"Table index {table_index} out of range (1 to {len(doc.tables)}).")

            table = doc.tables[table_index - 1]
            while len(table.rows) > 1:
                tr = table.rows[-1]._tr
                tr.getparent().remove(tr)

            num_cols = len(table.columns)
            for row in new_rows_data:
                new_r = table.add_row()
                for c_i, val in enumerate(row[:num_cols]):
                    new_r.cells[c_i].text = str(val)

            doc.save(str(staged))
            shutil.copy2(str(staged), str(out))

        logger.info(f"Partially regenerated table {table_index} in {out}")
        return str(out)

    @classmethod
    def regenerate_cell(
        cls,
        docx_path: str,
        table_index: int,
        row_index: int,
        col_index: int,
        new_text: str,
        output_path: Optional[str] = None
    ) -> str:
        """Modifies a single table cell in-place (or to output_path) while preserving other runs."""
        out = Path(output_path or docx_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="opengen_cell_") as tmp_dir:
            staged = Path(tmp_dir) / "staged.docx"
            shutil.copy2(docx_path, staged)
            doc = docx.Document(str(staged))

            if table_index < 0 or table_index >= len(doc.tables):
                raise ValueError(f"Table index {table_index} out of range (0 to {len(doc.tables) - 1}).")
            table = doc.tables[table_index]

            if row_index < 0 or row_index >= len(table.rows):
                raise ValueError(f"Row index {row_index} out of range (0 to {len(table.rows) - 1}).")
            row = table.rows[row_index]

            if col_index < 0 or col_index >= len(row.cells):
                raise ValueError(f"Column index {col_index} out of range (0 to {len(row.cells) - 1}).")

            cell = row.cells[col_index]
            if cell.paragraphs and cell.paragraphs[0].runs:
                cell.paragraphs[0].runs[0].text = new_text
                for r in cell.paragraphs[0].runs[1:]:
                    r.text = ""
            else:
                cell.text = new_text

            doc.save(str(staged))
            shutil.copy2(str(staged), str(out))

        logger.info(f"Partially regenerated cell ({table_index}, {row_index}, {col_index}) in {out}")
        return str(out)
