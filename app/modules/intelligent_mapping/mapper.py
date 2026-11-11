"""
Module 4: Intelligent Information Mapping.
Maps template requirements to extracted reference data, resolves semantic links,
detects conflicts, maps table columns, and prevents hallucination.
"""
import re
import logging
from typing import List, Dict, Any, Optional

from app.models.template_profile import TemplateProfile
from app.models.extracted_info import ExtractedInformation, ExtractedField
from app.models.mapping import (
    FieldMapping, TableMapping, ConflictItem, MappingReport
)
from app.modules.token_optimization.ai_router import AIRouter
from app.modules.intelligent_mapping.validator import AntiHallucinationValidator

logger = logging.getLogger(__name__)

# Common synonyms dictionary for direct fast matching
SYNONYM_GROUPS = [
    {"name", "full_name", "student_name", "candidate_name", "client_name", "applicant_name", "employee_name"},
    {"dob", "date_of_birth", "birthdate", "birth_date"},
    {"id", "student_id", "roll_number", "registration_number", "id_number", "candidate_id"},
    {"gpa", "cgpa", "grade_point_average", "marks", "percentage", "score"},
    {"email", "email_address", "e_mail", "mail"},
    {"phone", "telephone", "mobile", "phone_number", "contact_number"},
    {"address", "residential_address", "home_address", "location"},
    {"degree", "program", "course", "major", "qualification"},
    {"university", "institution", "college", "school", "organization", "company"},
    {"date", "issue_date", "document_date", "submission_date", "current_date"},
    {"amount", "total", "total_amount", "fee", "tuition_fee", "salary", "balance"}
]

class IntelligentMapper:
    """Performs intelligent semantic mapping between template and reference data."""

    def __init__(self, ai_router: Optional[AIRouter] = None):
        self.ai_router = ai_router or AIRouter()

    def map_document(
        self,
        template_profile: TemplateProfile,
        reference_docs: List[ExtractedInformation],
        additional_text: Optional[str] = None,
        instruction: Optional[str] = None,
        user_clarifications: Optional[Dict[str, Any]] = None
    ) -> MappingReport:
        user_clarifications = user_clarifications or {}
        mappings: Dict[str, FieldMapping] = {}
        missing_fields: List[str] = []
        conflicts: List[ConflictItem] = []
        used_ref_keys = set()

        # Aggregate all reference fields into a lookup list
        all_ref_fields: List[ExtractedField] = []
        for doc in reference_docs:
            all_ref_fields.extend(doc.fields)

        # 1. Collect required fields from placeholders
        required_fields = {p.field_name for p in template_profile.placeholders if p.field_name}

        # 2. Extract potential fields from additional text if present
        if additional_text:
            self._parse_additional_text(additional_text, all_ref_fields)

        # 3. Direct & Synonym Matching
        for req_field in required_fields:
            # Check if user already provided clarification
            if req_field in user_clarifications:
                val = user_clarifications[req_field]
                mappings[req_field] = FieldMapping(
                    template_field=req_field,
                    mapped_value=val,
                    source="user_input",
                    confidence=1.0,
                    status="user_provided",
                    match_type="direct"
                )
                continue

            # Look for exact or synonym match
            candidates = self._find_candidates(req_field, all_ref_fields)

            if len(candidates) == 1:
                cand = candidates[0]
                mappings[req_field] = FieldMapping(
                    template_field=req_field,
                    mapped_value=cand.value,
                    source=cand.source,
                    source_page=cand.page,
                    confidence=cand.confidence,
                    status="verified",
                    match_type="direct" if cand.field.lower() == req_field.lower() else "semantic",
                    notes=cand.context
                )
                used_ref_keys.add(cand.field)

            elif len(candidates) > 1:
                # Check if candidates agree on value
                unique_values = {str(c.value).strip().lower() for c in candidates}
                if len(unique_values) == 1:
                    best = max(candidates, key=lambda c: c.confidence)
                    mappings[req_field] = FieldMapping(
                        template_field=req_field,
                        mapped_value=best.value,
                        source=best.source,
                        source_page=best.page,
                        confidence=best.confidence,
                        status="verified",
                        match_type="direct",
                        notes=best.context
                    )
                    used_ref_keys.add(best.field)
                else:
                    # Conflicting values across sources
                    conflict_item = ConflictItem(
                        field_name=req_field,
                        candidates=[
                            {"value": c.value, "source": c.source, "page": c.page, "confidence": c.confidence}
                            for c in candidates
                        ]
                    )
                    conflicts.append(conflict_item)
                    # Pick highest confidence as default tentative
                    best = max(candidates, key=lambda c: c.confidence)
                    mappings[req_field] = FieldMapping(
                        template_field=req_field,
                        mapped_value=best.value,
                        source=best.source,
                        source_page=best.page,
                        confidence=best.confidence,
                        status="conflict",
                        match_type="semantic",
                        notes=f"Conflicting values detected across sources for {req_field}"
                    )

            else:
                # Not found yet
                missing_fields.append(req_field)

        # 4. AI Semantic Matching for remaining missing fields
        if missing_fields and all_ref_fields:
            still_missing = self._resolve_with_ai(
                missing_fields=missing_fields,
                all_ref_fields=all_ref_fields,
                mappings=mappings,
                instruction=instruction
            )
            missing_fields = still_missing

        # 5. Table-to-Table Mapping
        table_mappings = self._map_tables(template_profile, reference_docs)

        # 6. Anti-Hallucination Audit
        AntiHallucinationValidator.audit_all(mappings)

        # Identify unused reference fields
        all_candidate_names = {f.field for f in all_ref_fields}
        unused = list(all_candidate_names - used_ref_keys)

        # Build clarification questions if missing or conflicting fields exist
        clarification_questions = []
        for m in missing_fields:
            clarification_questions.append(f"Please provide the value for required field '{m}'.")
        for c in conflicts:
            options_str = ", ".join([f"'{opt['value']}' ({opt['source']})" for opt in c.candidates])
            clarification_questions.append(f"Field '{c.field_name}' has conflicting values: {options_str}. Which one should be used?")

        requires_clarification = len(clarification_questions) > 0 and len(missing_fields) > 0

        return MappingReport(
            mappings=mappings,
            table_mappings=table_mappings,
            missing_fields=missing_fields,
            conflicting_fields=conflicts,
            unused_reference_fields=unused[:30],
            requires_user_clarification=requires_clarification,
            clarification_questions=clarification_questions,
            status="pending_clarification" if requires_clarification else "ready"
        )

    def _find_candidates(self, target_field: str, ref_fields: List[ExtractedField]) -> List[ExtractedField]:
        target_norm = target_field.lower().strip()
        candidates = []

        # 1. Exact match
        for f in ref_fields:
            if f.field.lower() == target_norm:
                candidates.append(f)
        if candidates:
            return candidates

        # 2. Synonym group match
        syn_set = None
        for group in SYNONYM_GROUPS:
            if target_norm in group or any(target_norm.endswith(item) for item in group):
                syn_set = group
                break

        if syn_set:
            for f in ref_fields:
                f_norm = f.field.lower()
                if f_norm in syn_set or any(f_norm.endswith(item) for item in syn_set):
                    candidates.append(f)

        return candidates

    def _parse_additional_text(self, text: str, ref_fields: List[ExtractedField]):
        lines = text.split("\n")
        for line in lines:
            if ":" in line:
                parts = line.split(":", 1)
                k = re.sub(r'[\s/]+', '_', parts[0].strip()).lower()
                v = parts[1].strip()
                if k and v:
                    ref_fields.append(ExtractedField(
                        field=k,
                        value=v,
                        source="user_additional_text",
                        page=1,
                        confidence=1.0,
                        field_type="user_text",
                        context=line
                    ))

    def _resolve_with_ai(
        self,
        missing_fields: List[str],
        all_ref_fields: List[ExtractedField],
        mappings: Dict[str, FieldMapping],
        instruction: Optional[str] = None
    ) -> List[str]:
        # Formulate compact prompt with target fields and available evidence
        available_summary = [
            f"{f.field}: {f.value} (source: {f.source})"
            for f in all_ref_fields[:60]
        ]
        prompt = (
            f"You are matching document fields. Instructions: {instruction or 'Map accurately. Never invent facts.'}\n"
            f"Target missing template fields: {missing_fields}\n"
            f"Available reference facts:\n" + "\n".join(available_summary) + "\n\n"
            f"If a reference fact matches a target missing field (even with different wording), output JSON:\n"
            f'{{"matches": [{{"template_field": "...", "value": "...", "source": "...", "confidence": 0.9}}]}}\n'
            f"If no match exists, do NOT include it in matches."
        )

        res = self.ai_router.route_task("mapping", prompt)
        matches = res.get("matches", [])
        
        still_missing = list(missing_fields)
        for m in matches:
            t_field = m.get("template_field")
            val = m.get("value")
            if t_field in still_missing and val:
                mappings[t_field] = FieldMapping(
                    template_field=t_field,
                    mapped_value=val,
                    source=m.get("source", "reference_ai"),
                    confidence=float(m.get("confidence", 0.85)),
                    status="verified",
                    match_type="semantic",
                    notes="AI semantic resolution"
                )
                still_missing.remove(t_field)

        return still_missing

    def _map_tables(self, template_profile: TemplateProfile, reference_docs: List[ExtractedInformation]) -> List[TableMapping]:
        table_mappings = []
        all_ref_tables = []
        for doc in reference_docs:
            all_ref_tables.extend(doc.tables)

        if not template_profile.tables or not all_ref_tables:
            return table_mappings

        for t_idx, templ_tab in enumerate(template_profile.tables):
            # Find reference table with matching or compatible columns
            best_ref = None
            best_score = -1

            for ref_tab in all_ref_tables:
                score = 0
                if ref_tab.headers:
                    # Count overlap with any cells in template table header
                    templ_first_row = [c.text.lower() for c in templ_tab.cells if c.row_idx == 0]
                    for h in ref_tab.headers:
                        if any(h.lower() in t_cell or t_cell in h.lower() for t_cell in templ_first_row if t_cell):
                            score += 2
                    if len(ref_tab.rows) > 0:
                        score += 1
                if score > best_score:
                    best_score = score
                    best_ref = ref_tab

            if best_ref and best_score > 0:
                table_mappings.append(TableMapping(
                    template_table_index=templ_tab.table_index,
                    source_table_index=best_ref.table_index,
                    source_document=best_ref.source,
                    rows_data=best_ref.rows,
                    confidence=0.92
                ))

        return table_mappings
