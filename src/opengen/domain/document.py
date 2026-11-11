"""
Domain models representing documents, templates, extracted facts, mappings, and validation reports.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# --- Geometry & Font Profiles ---
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
    alignment: Optional[str] = "LEFT"
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
    column_widths_inches: List[float] = Field(default_factory=list)
    has_header: bool = False
    repeat_header: bool = False
    cells: List[TableCellProfile] = Field(default_factory=list)
    borders: Dict[str, Any] = Field(default_factory=dict)
    alignment: str = "CENTER"
    caption: Optional[str] = None

class PlaceholderProfile(BaseModel):
    raw_key: str
    field_name: str
    context: str = ""
    location_type: str = "body"
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
    page_size: str = "A4"
    page_width_inches: float = 8.27
    page_height_inches: float = 11.69
    orientation: str = "portrait"
    margins: Margins = Field(default_factory=Margins)
    headers: List[str] = Field(default_factory=list)
    footers: List[str] = Field(default_factory=list)
    has_page_numbers: bool = False

class TemplateProfile(BaseModel):
    document_type: str = "general"
    file_type: str = "docx"  # "docx" or "pdf"
    file_hash: str = ""
    original_filename: str = ""
    page_size: str = "A4"
    orientation: str = "portrait"
    margins: Margins = Field(default_factory=Margins)
    sections: List[SectionProfile] = Field(default_factory=list)
    headings: List[Dict[str, Any]] = Field(default_factory=list)
    tables: List[TableProfile] = Field(default_factory=list)
    styles: Dict[str, FontProfile] = Field(default_factory=dict)
    headers: List[str] = Field(default_factory=list)
    footers: List[str] = Field(default_factory=list)
    images: List[ImageProfile] = Field(default_factory=list)
    placeholders: List[PlaceholderProfile] = Field(default_factory=list)
    total_pages_approx: int = 1
    structure_summary: str = ""

# --- Reference Knowledge Extraction ---
class ExtractedField(BaseModel):
    field: str
    value: Any
    source: str
    page: int = 1
    confidence: float = 1.0
    field_type: str = "text"
    context: Optional[str] = None
    raw_snippet: Optional[str] = None

class ExtractedTable(BaseModel):
    table_index: int
    source: str
    page: int = 1
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    confidence: float = 1.0
    raw_markdown: Optional[str] = None

class ExtractedInformation(BaseModel):
    document_id: str
    filename: str
    file_hash: str
    fields: List[ExtractedField] = Field(default_factory=list)
    tables: List[ExtractedTable] = Field(default_factory=list)
    headings: List[Dict[str, Any]] = Field(default_factory=list)
    raw_text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ocr_used: bool = False
    total_pages: int = 1

# --- Semantic Mapping & Anti-Hallucination ---
class FieldMapping(BaseModel):
    template_field: str
    mapped_value: Any
    source: str = ""
    source_page: Optional[int] = None
    confidence: float = 1.0
    status: str = "verified"     # verified, missing, ambiguous, conflict, user_provided
    match_type: str = "direct"  # direct, semantic, contextual, user_defined
    notes: Optional[str] = None

class TableMapping(BaseModel):
    template_table_index: int
    source_table_index: int
    source_document: str
    column_mapping: Dict[str, str] = Field(default_factory=dict)
    rows_data: List[List[str]] = Field(default_factory=list)
    confidence: float = 1.0

class ConflictItem(BaseModel):
    field_name: str
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    resolved_value: Optional[Any] = None
    reason: Optional[str] = None

class MappingReport(BaseModel):
    mappings: Dict[str, FieldMapping] = Field(default_factory=dict)
    table_mappings: List[TableMapping] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    conflicting_fields: List[ConflictItem] = Field(default_factory=list)
    unused_reference_fields: List[str] = Field(default_factory=list)
    requires_user_clarification: bool = False
    clarification_questions: List[str] = Field(default_factory=list)
    status: str = "ready"

# --- Visual Validation ---
class VisualIssue(BaseModel):
    issue_type: str  # overflow, blank_page, broken_table, misaligned, font_inconsistency, margin_violation
    page_number: int
    severity: str = "warning"
    description: str
    rect: Optional[List[float]] = None
    suggested_fix: Optional[str] = None

class PageVisualInspection(BaseModel):
    page_number: int
    has_text_overflow: bool = False
    is_blank: bool = False
    has_broken_table: bool = False
    has_margin_clip: bool = False
    font_consistency_score: float = 1.0
    detected_elements: Dict[str, int] = Field(default_factory=dict)
    issues: List[VisualIssue] = Field(default_factory=list)

class FormattingValidationReport(BaseModel):
    is_valid: bool = True
    iteration: int = 1
    template_page_count: int = 1
    generated_page_count: int = 1
    page_count_match: bool = True
    pages: List[PageVisualInspection] = Field(default_factory=list)
    total_issues: int = 0
    issues_summary: List[str] = Field(default_factory=list)
    corrections_applied: List[str] = Field(default_factory=list)
    status: str = "passed"
