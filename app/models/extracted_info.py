"""
Data models representing extracted information from reference documents.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ExtractedField(BaseModel):
    field: str
    value: Any
    source: str
    page: int = 1
    confidence: float = 1.0
    field_type: str = "text"   # text, date, currency, number, list, person_name, organization
    context: Optional[str] = None
    raw_snippet: Optional[str] = None

class ExtractedTable(BaseModel):
    table_index: int
    source: str
    page: int = 1
    headers: List[str] = []
    rows: List[List[str]] = []
    confidence: float = 1.0
    raw_markdown: Optional[str] = None

class ExtractedInformation(BaseModel):
    document_id: str
    filename: str
    file_hash: str
    fields: List[ExtractedField] = []
    tables: List[ExtractedTable] = []
    headings: List[Dict[str, Any]] = []
    raw_text: str = ""
    metadata: Dict[str, Any] = {}
    ocr_used: bool = False
    total_pages: int = 1
