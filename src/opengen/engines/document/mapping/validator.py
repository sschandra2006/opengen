"""
Anti-Hallucination Validator for Module 4.
Asserts that extracted values are backed by reference evidence before populating templates.
"""
import re
import logging
from typing import Dict, Any, List
from opengen.domain.document import FieldMapping

logger = logging.getLogger(__name__)

class AntiHallucinationValidator:
    """Verifies that mapped values actually exist in reference documents."""

    @classmethod
    def validate_mapping(cls, mapping: FieldMapping, reference_text: str) -> bool:
        """
        Validates that mapping.mapped_value can be found or verified in reference_text.
        Returns True if verified, False if hallucination suspected.
        """
        val_str = str(mapping.mapped_value).strip().lower()
        if not val_str:
            return False

        ref_lower = reference_text.lower()

        # 1. Exact or substring match
        if val_str in ref_lower:
            return True

        # 2. Number / currency normalization match
        clean_num = re.sub(r'[\$,£,€,¥\s,]', '', val_str)
        if len(clean_num) > 1 and clean_num in re.sub(r'[\$,£,€,¥\s,]', '', ref_lower):
            return True

        # 3. Token-level overlap for multi-word phrases (e.g. names, degrees)
        tokens = [t for t in val_str.split() if len(t) > 2]
        if tokens:
            matches = sum(1 for t in tokens if t in ref_lower)
            if matches / len(tokens) >= 0.75:
                return True

        logger.warning(f"Anti-hallucination alert: Field '{mapping.template_field}' with value '{mapping.mapped_value}' could not be verified in reference text.")
        return False
