"""
Strict Anti-Hallucination and Verification Engine for Module 4.
Ensures that no personal details, qualifications, dates, financial figures,
or official items are invented without explicit reference source or user confirmation.
"""
from typing import Dict, Any, List
from app.models.mapping import FieldMapping

FORBIDDEN_INVENTED_CATEGORIES = {
    "name", "student_name", "candidate_name", "client_name", "author",
    "date", "dob", "birth_date", "issue_date", "expiry_date", "graduation_date",
    "gpa", "cgpa", "grade", "qualification", "degree", "marks", "score",
    "financial", "amount", "salary", "fee", "cost", "total", "price", "tax",
    "signature", "stamp", "certificate_number", "id_number", "passport", "ssn"
}

class AntiHallucinationValidator:
    """Verifies that all mapped values originate strictly from reference or user input."""

    @classmethod
    def validate_mapping(cls, mapping: FieldMapping) -> bool:
        field_norm = mapping.template_field.lower()

        # If field belongs to sensitive category and has no verified source
        is_sensitive = any(cat in field_norm for cat in FORBIDDEN_INVENTED_CATEGORIES)
        
        if is_sensitive:
            if not mapping.source and mapping.status != "user_provided":
                mapping.status = "missing"
                mapping.notes = "Sensitive field requires verified source document or explicit user input. Generation prevented hallucination."
                return False

        return True

    @classmethod
    def audit_all(cls, mappings: Dict[str, FieldMapping]) -> List[str]:
        warnings = []
        for key, m in mappings.items():
            if not cls.validate_mapping(m):
                warnings.append(f"Field '{key}' has no verifiable reference evidence and cannot be auto-filled.")
        return warnings
