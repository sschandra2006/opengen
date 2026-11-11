"""
Advanced Table Builder for python-docx.
Enforces borders, cell padding, row split prevention (cantSplit),
repeated header rows (tblHeader), column widths, and cell alignment.
"""
from typing import List, Optional
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

class TableBuilder:
    """Utilities for constructing and formatting professional Word tables."""

    @staticmethod
    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        """Sets internal cell margins/padding in dxa (1 pt = 20 dxa)."""
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for margin_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            node = OxmlElement(f'w:{margin_name}')
            node.set(qn('w:w'), str(val))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    @staticmethod
    def set_cell_background(cell, color_hex: str):
        """Sets cell background shading."""
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

    @staticmethod
    def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
        """Sets clean subtle borders across the entire table."""
        tblPr = table._tbl.tblPr
        borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'  <w:left w:val="none"/>'
            f'  <w:right w:val="none"/>'
            f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'  <w:insideV w:val="none"/>'
            f'</w:tblBorders>'
        )
        tblPr.append(borders)

    @classmethod
    def apply_advanced_properties(cls, table, col_widths: Optional[List[float]] = None):
        """
        Applies cantSplit on all rows and tblHeader on row 0 to prevent broken tables.
        Also applies column widths and alignments.
        """
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for r_idx, row in enumerate(table.rows):
            trPr = row._tr.get_or_add_trPr()
            
            # Prevent row from splitting across pages
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))

            # Repeat header on subsequent pages if first row
            if r_idx == 0:
                trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))

            # Set widths and padding per cell
            for c_idx, cell in enumerate(row.cells):
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                cls.set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
                if col_widths and c_idx < len(col_widths):
                    cell.width = Inches(col_widths[c_idx])

        cls.set_table_borders(table)
