"""
Unified token and USD cost calculation and tracking.
Supports per-job CostTracker isolation so generations never bleed cost metrics across runs.
"""
from typing import Dict, Any
from opengen.domain.provider import TokenCostReport
from opengen.providers.registry import MODEL_REGISTRY


class CostTracker:
    """Tracks token usage across pipeline stages and computes exact USD expenditure."""

    def __init__(self):
        self.report = TokenCostReport()

    def reset(self):
        """Resets metrics for a clean generation run."""
        self.report = TokenCostReport()

    def add_report(self, sub_report: TokenCostReport):
        """Merges a per-call TokenCostReport into this tracker."""
        if sub_report.model_used:
            self.report.model_used = sub_report.model_used
        self.report.input_tokens += sub_report.input_tokens
        self.report.output_tokens += sub_report.output_tokens
        self.report.cached_tokens += sub_report.cached_tokens
        self.report.cost_usd = round(self.report.cost_usd + sub_report.cost_usd, 6)
        self.report.local_operations_count += sub_report.local_operations_count

    def record_usage(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ):
        self.report.model_used = model_name
        self.report.input_tokens += input_tokens
        self.report.output_tokens += output_tokens
        self.report.cached_tokens += cached_tokens

        # Lookup rates
        cap = MODEL_REGISTRY.get(model_name)
        if cap:
            in_cost = (input_tokens / 1_000_000.0) * cap.input_cost_per_m
            out_cost = (output_tokens / 1_000_000.0) * cap.output_cost_per_m
            cache_cost = (cached_tokens / 1_000_000.0) * cap.cached_cost_per_m
            self.report.cost_usd = round(self.report.cost_usd + in_cost + out_cost + cache_cost, 6)

    def record_local_operation(self, count: int = 1):
        self.report.local_operations_count += count

    def get_summary(self) -> Dict[str, Any]:
        return self.report.model_dump()

    def get_aggregate_cost(self) -> Dict[str, Any]:
        return {
            "total_cost_usd": self.report.cost_usd,
            "input_tokens": self.report.input_tokens,
            "output_tokens": self.report.output_tokens,
            "cached_tokens": self.report.cached_tokens,
            "local_operations": self.report.local_operations_count,
        }


cost_tracker = CostTracker()
