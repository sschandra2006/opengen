"""
Data models representing the structural profile of a document template (DOCX or PDF).
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Margins(BaseModel):
    top: float = 1.0       # in inches
    bottom: float = 1.0
    left: float = 1.0
    right: float = 1.0

class FontProfile(BaseModel):
    name: Optional[str] = "Calibri"
    size_pt: Optional[float] = 11.0
    bold: Optional[bool] = False
    italic: Optional[bool] = False
    color_rgb: Optional[str] = "000000"
    alignment: Optional[str] = "LEFT"  # LEFT, CENTER, RIGHT, JUSTIFY
    line_spacing: Optional[float] = 1.15
    space_after_pt: Optional[float] = 6.0
    space_before_pt: Optional[float] = 0.0

class TableCellProfile(BaseModel):
    row_idx: int
    col_idx: int
    text: str = ""
    font: Optional[FontProfile] = None
    width_inches: Optional[float] = None
    background_color: Optional[str] = None
    is_merged: bool = False
    colspan: int = 1
    rowspan: int = 1
    alignment: str = "LEFT"

class TableProfile(BaseModel):
    table_index: int
    num_rows: int
    num_cols: int
    column_widths_inches: List[float] = []
    has_header: bool = False
    repeat_header: bool = False
    cells: List[TableCellProfile] = []
    borders: Dict[str, Any] = {}
    alignment: str = "CENTER"
    caption: Optional[str] = None

class PlaceholderProfile(BaseModel):
    raw_key: str              # e.g., "{{student_name}}" or "[Company Name]"
    field_name: str           # e.g., "student_name" or "company_name"
    context: str = ""         # Surrounding sentence or paragraph
    location_type: str = "body" # body, table_cell, header, footer
    table_index: Optional[int] = None
    row_index: Optional[int] = None
    col_index: Optional[int] = None
    paragraph_index: Optional[int] = None
    run_font: Optional[FontProfile] = None

class ImageProfile(BaseModel):
    image_index: int
    filename: str
    width_inches: Optional[float] = None
    height_inches: Optional[float] = None
    is_header_or_logo: bool = False
    location: str = "body"
    rel_path: Optional[str] = None

class SectionProfile(BaseModel):
    section_index: int
    page_size: str = "A4"      # A4, LETTER, etc.
    page_width_inches: float = 8.27
    page_height_inches: float = 11.69
    orientation: str = "portrait"
    margins: Margins = Margins()
    headers: List[str] = []
    footers: List[str] = []
    has_page_numbers: bool = False

class TemplateProfile(BaseModel):
    document_type: str = "general"
    file_type: str = "docx"    # "docx" or "pdf"
    file_hash: str = ""
    original_filename: str = ""
    page_size: str = "A4"
    orientation: str = "portrait"
    margins: Margins = Margins()
    sections: List[SectionProfile] = []
    headings: List[Dict[str, Any]] = []
    tables: List[TableProfile] = []
    styles: Dict[str, FontProfile] = {}
    headers: List[str] = []
    footers: List[str] = []
    images: List[ImageProfile] = []
    placeholders: List[PlaceholderProfile] = []
    total_pages_approx: int = 1
    structure_summary: str = ""
