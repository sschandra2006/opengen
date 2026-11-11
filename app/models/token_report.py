"""
Data models representing token optimization tracking and telemetry.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class TokenUsageReport(BaseModel):
    template_analysis_tokens: int = 0
    information_extraction_tokens: int = 0
    mapping_tokens: int = 0
    generation_tokens: int = 0
    validation_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    local_operations_count: int = 0
    qwen_local_tokens: int = 0
    gemini_cloud_tokens: int = 0
    estimated_cost_savings_usd: float = 0.0
    cache_hits: int = 0

    def add_gemini_tokens(self, stage: str, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.gemini_cloud_tokens += (input_tokens + output_tokens)
        if stage == "template_analysis":
            self.template_analysis_tokens += (input_tokens + output_tokens)
        elif stage == "information_extraction":
            self.information_extraction_tokens += (input_tokens + output_tokens)
        elif stage == "mapping":
            self.mapping_tokens += (input_tokens + output_tokens)
        elif stage == "generation":
            self.generation_tokens += (input_tokens + output_tokens)
        elif stage == "validation":
            self.validation_tokens += (input_tokens + output_tokens)

    def add_local_operation(self, count: int = 1):
        self.local_operations_count += count
