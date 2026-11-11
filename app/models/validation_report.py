"""
Data models representing the visual formatting and layout validation report.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class VisualIssue(BaseModel):
    issue_type: str         # overflow, blank_page, broken_table, misaligned, font_inconsistency, margin_violation
    page_number: int
    severity: str = "warning" # error, warning, info
    description: str
    rect: Optional[List[float]] = None # [x0, y0, x1, y1] if localized
    suggested_fix: Optional[str] = None

class PageVisualInspection(BaseModel):
    page_number: int
    has_text_overflow: bool = False
    is_blank: bool = False
    has_broken_table: bool = False
    has_margin_clip: bool = False
    font_consistency_score: float = 1.0
    detected_elements: Dict[str, int] = {} # {"images": 1, "tables": 1, "text_blocks": 5}
    issues: List[VisualIssue] = []

class FormattingValidationReport(BaseModel):
    is_valid: bool = True
    iteration: int = 1
    template_page_count: int = 1
    generated_page_count: int = 1
    page_count_match: bool = True
    pages: List[PageVisualInspection] = []
    total_issues: int = 0
    issues_summary: List[str] = []
    corrections_applied: List[str] = []
    status: str = "passed" # passed, auto_corrected, warning, failed
