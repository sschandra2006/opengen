"""
Intelligent Information Mapping Engine.
Maps template requirements to extracted reference data, resolves semantic links,
detects conflicts, maps table columns, and prevents hallucination.
"""
import re
import logging
from typing import List, Dict, Any, Optional

from opengen.domain.document import (
    TemplateProfile, ExtractedInformation, ExtractedField,
    FieldMapping, TableMapping, ConflictItem, MappingReport
)
from opengen.providers.manager import ProviderManager, provider_manager
from opengen.engines.document.mapping.validator import AntiHallucinationValidator

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

    def __init__(self, provider_mgr: Optional[ProviderManager] = None):
        self.provider_manager = provider_mgr or provider_manager

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
                unique_vals = {str(c.value).strip().lower(): c for c in candidates}
                if len(unique_vals) == 1:
                    chosen = candidates[0]
                    mappings[req_field] = FieldMapping(
                        template_field=req_field,
                        mapped_value=chosen.value,
                        source=chosen.source,
                        source_page=chosen.page,
                        confidence=chosen.confidence,
                        status="verified",
                        match_type="semantic"
                    )
                else:
                    conflict = ConflictItem(
                        field_name=req_field,
                        candidates=[
                            {"value": c.value, "source": c.source, "page": c.page, "confidence": c.confidence}
                            for c in candidates
                        ],
                        reason=f"Multiple conflicting values detected for '{req_field}' across reference documents."
                    )
                    conflicts.append(conflict)
            else:
                missing_fields.append(req_field)

        # 4. Map Tables
        table_mappings = self._map_tables(template_profile, reference_docs)

        # 5. Anti-Hallucination Audit
        combined_ref_text = "\n".join(doc.raw_text for doc in reference_docs)
        if additional_text:
            combined_ref_text += f"\n{additional_text}"

        for f_name, f_map in list(mappings.items()):
            if f_map.status == "verified":
                is_legit = AntiHallucinationValidator.validate_mapping(f_map, combined_ref_text)
                if not is_legit:
                    logger.warning(f"Removing unverified field mapping: {f_name}")
                    del mappings[f_name]
                    missing_fields.append(f_name)

        # 6. User Clarification Triggers
        clarification_questions = []
        requires_clarification = False

        if conflicts:
            requires_clarification = True
            for c in conflicts:
                opts = ", ".join(f"'{opt['value']}' (from {opt['source']})" for opt in c.candidates)
                clarification_questions.append(
                    f"Conflicting values found for '{c.field_name}': {opts}. Which one should be used?"
                )

        if missing_fields:
            important_missing = [
                m for m in missing_fields
                if any(kw in m for kw in ["name", "id", "date", "gpa", "grade", "amount", "total"])
            ]
            if important_missing:
                requires_clarification = True
                clarification_questions.append(
                    f"The following required fields could not be found in reference files: {', '.join(important_missing)}. Please provide values."
                )

        unused_keys = [f.field for f in all_ref_fields if f.field not in used_ref_keys]

        return MappingReport(
            mappings=mappings,
            table_mappings=table_mappings,
            missing_fields=missing_fields,
            conflicting_fields=conflicts,
            unused_reference_fields=list(set(unused_keys)),
            requires_user_clarification=requires_clarification,
            clarification_questions=clarification_questions,
            status="pending_clarification" if requires_clarification else "ready"
        )

    def _find_candidates(self, target_key: str, ref_fields: List[ExtractedField]) -> List[ExtractedField]:
        t_clean = re.sub(r'[^a-zA-Z0-9]', '', target_key).lower()
        exact_matches = []
        for f in ref_fields:
            f_clean = re.sub(r'[^a-zA-Z0-9]', '', f.field).lower()
            if f_clean == t_clean:
                exact_matches.append(f)

        if exact_matches:
            return exact_matches

        synonyms = self._get_synonyms(target_key)
        syn_matches = []
        for f in ref_fields:
            f_norm = f.field.lower()
            if f_norm in synonyms or any(s in f_norm for s in synonyms if len(s) > 3):
                syn_matches.append(f)

        return syn_matches

    def _get_synonyms(self, key: str) -> set:
        clean = key.lower().strip()
        for group in SYNONYM_GROUPS:
            if clean in group or any(member in clean for member in group):
                return group
        return {clean}

    def _map_tables(self, template_profile: TemplateProfile, reference_docs: List[ExtractedInformation]) -> List[TableMapping]:
        table_mappings: List[TableMapping] = []
        all_ref_tables = []
        for doc in reference_docs:
            for t in doc.tables:
                all_ref_tables.append((doc.filename, t))

        if not all_ref_tables or not template_profile.tables:
            return table_mappings

        for t_prof in template_profile.tables:
            t_idx = t_prof.table_index
            for filename, ref_table in all_ref_tables:
                if ref_table.rows:
                    t_map = TableMapping(
                        template_table_index=t_idx,
                        source_table_index=ref_table.table_index,
                        source_document=filename,
                        column_mapping={h: h for h in ref_table.headers},
                        rows_data=ref_table.rows,
                        confidence=ref_table.confidence
                    )
                    table_mappings.append(t_map)
                    break

        return table_mappings

    def _parse_additional_text(self, text: str, ref_fields: List[ExtractedField]):
        lines = text.strip().split("\n")
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                k_clean = re.sub(r'[\s/]+', '_', k.strip()).lower()
                v_clean = v.strip()
                if k_clean and v_clean:
                    ref_fields.append(ExtractedField(
                        field=k_clean,
                        value=v_clean,
                        source="additional_text",
                        page=1,
                        confidence=1.0,
                        field_type="user_text",
                        context=line
                    ))
