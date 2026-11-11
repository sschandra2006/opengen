"""
Token Usage Tracker for Module 8: Token Optimization Engine.
Tracks tokens across all pipeline stages, distinguishing local Ollama vs cloud Gemini.
"""
from typing import Dict, Any
from app.models.token_report import TokenUsageReport

class TokenTracker:
    def __init__(self):
        self.report = TokenUsageReport()

    def record_gemini(self, stage: str, input_tokens: int, output_tokens: int):
        self.report.add_gemini_tokens(stage, input_tokens, output_tokens)

    def record_local_llm(self, tokens_approx: int):
        self.report.qwen_local_tokens += tokens_approx
        # Every local token saved cloud expense: estimate ~$0.15 per 1M tokens
        self.report.estimated_cost_savings_usd += (tokens_approx / 1_000_000.0) * 0.15

    def record_local_op(self, count: int = 1):
        self.report.add_local_operation(count)

    def record_cache_hit(self):
        self.report.cache_hits += 1

    def get_summary(self) -> Dict[str, Any]:
        return self.report.model_dump()
