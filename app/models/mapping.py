"""
Data models representing the intelligent mapping between template profiles and reference data.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

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
    column_mapping: Dict[str, str] = {}
    rows_data: List[List[str]] = []
    confidence: float = 1.0

class ConflictItem(BaseModel):
    field_name: str
    candidates: List[Dict[str, Any]] = [] # [{value: '...', source: '...', page: 1, confidence: 0.9}]
    resolved_value: Optional[Any] = None
    reason: Optional[str] = None

class MappingReport(BaseModel):
    mappings: Dict[str, FieldMapping] = {}
    table_mappings: List[TableMapping] = []
    missing_fields: List[str] = []
    conflicting_fields: List[ConflictItem] = []
    unused_reference_fields: List[str] = []
    requires_user_clarification: bool = False
    clarification_questions: List[str] = []
    status: str = "ready" # ready, pending_clarification, incomplete
