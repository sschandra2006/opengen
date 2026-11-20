"""
Token Budgeter and Chunking Governor for OpenGen.
Enforces mathematical output token limits and dynamic catalog/document chunking
to prevent quadratic KV-cache growth and out-of-memory errors on small GPUs.
"""
from typing import List, TypeVar, Optional
from opengen.hardware.models import AdaptiveExecutionPolicy

T = TypeVar("T")


class TokenBudgeter:
    """Manages token budgeting and input/output chunking based on hardware tier."""

    @classmethod
    def clamp_max_output_tokens(
        cls,
        policy: AdaptiveExecutionPolicy,
        requested_max_tokens: Optional[int] = None,
        estimated_schema_tokens: int = 500
    ) -> int:
        """
        Determines the safe completion token limit for the current hardware tier.
        Guarantees that generation will never blow out available memory headroom.
        """
        tier_cap = policy.max_output_tokens

        if requested_max_tokens is not None and requested_max_tokens > 0:
            # User provided a target, clamp to hardware safety ceiling
            return min(requested_max_tokens, tier_cap)

        # Automatic allocation: ensure schema can fit comfortably within safety limit
        return min(max(estimated_schema_tokens, 512), tier_cap)

    @classmethod
    def clamp_context_window(
        cls,
        policy: AdaptiveExecutionPolicy,
        requested_context: Optional[int] = None
    ) -> int:
        """Clamps the input prompt context window according to hardware limits."""
        tier_cap = policy.max_llm_context
        if requested_context is not None and requested_context > 0:
            return min(requested_context, tier_cap)
        return tier_cap

    @classmethod
    def chunk_sequence(
        cls,
        items: List[T],
        policy: Optional[AdaptiveExecutionPolicy] = None,
        chunk_size_override: Optional[int] = None
    ) -> List[List[T]]:
        """
        Partitions large sequences (e.g., catalog SKUs, presentation sections)
        into hardware-safe batches so memory never accumulates unbounded in-flight.
        """
        if not items:
            return []

        effective_chunk_size = chunk_size_override or (policy.doc_chunk_size if policy else 10)
        effective_chunk_size = max(1, effective_chunk_size)

        return [
            items[i:i + effective_chunk_size]
            for i in range(0, len(items), effective_chunk_size)
        ]
