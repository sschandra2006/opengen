"""
Unit and Integration Tests for Advanced Token Reduction & Surgical Reflection.
Module 8 & UTRA (Universal Token-Reduction Architecture).
"""
import pytest
from unittest.mock import MagicMock, patch
from app.config import settings
from app.modules.token_optimization.ai_router import (
    AIRouter,
    ZERO_CHATTER_DIRECTIVE
)
from src.opengen.providers.manager import (
    NEGATIVE_AESTHETIC_INVARIANT,
    provider_manager
)


def test_zero_chatter_directives_presence():
    """Verifies that Zero-Chatter and Anti-Chatter constraints are strictly configured."""
    assert "ZERO-CHATTER DIRECTIVE" in ZERO_CHATTER_DIRECTIVE
    assert "Never include conversational text" in ZERO_CHATTER_DIRECTIVE or "Output ONLY" in ZERO_CHATTER_DIRECTIVE
    assert "ZERO-CHATTER DIRECTIVE" in NEGATIVE_AESTHETIC_INVARIANT


def test_default_model_alignment():
    """Verifies default local model is aligned to huihui-ai/qwen2.5-abliterated:7b."""
    assert "qwen2.5-abliterated" in settings.OLLAMA_MODEL
    from opengen.config import settings as src_settings
    assert "qwen2.5-abliterated" in src_settings.DEFAULT_LOCAL_MODEL


def test_airouter_call_dense_dsl_with_surgical_reflection():
    """Verifies that call_dense_dsl invokes surgical reflection when a line is malformed."""
    router = AIRouter()

    # Mock call_cloud to return a stream with 1 valid and 1 broken line
    initial_output = (
        "SKU-01|Fresh Milk|Dairy|60|55|1L|true\n"
        "BROKEN_MALFORMED_LINE\n"
    )
    repaired_line = "SKU-02|Fresh Curd|Dairy|40|35|500g|false"

    with patch.object(router, "call_cloud") as mock_cloud:
        # First call returns initial_output, second call (reflection) returns repaired_line
        mock_cloud.side_effect = [
            {"raw_text": initial_output},
            {"raw_text": repaired_line}
        ]

        items = router.call_dense_dsl(
            prompt="Extract items",
            delimiter="|",
            use_surgical_reflection=True
        )

        assert len(items) == 2
        assert items[0].sku == "SKU-01"
        assert items[1].sku == "SKU-02"
        assert items[1].name == "Fresh Curd"
        # Verify that mock_cloud was called twice: once for document, once for surgical repair
        assert mock_cloud.call_count == 2
        # Verify the second call prompt was surgical (targeted only broken line)
        repair_call_prompt = mock_cloud.call_args_list[1][0][0]
        assert "BROKEN_MALFORMED_LINE" in repair_call_prompt
        assert "Output ONLY the corrected single line" in repair_call_prompt
