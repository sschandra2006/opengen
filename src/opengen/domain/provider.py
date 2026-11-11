"""
Domain models for AI provider integration, tokens, and cost accounting.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class TokenCostReport(BaseModel):
    model_used: str = ""
    provider_used: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    cost_usd: float = 0.0
    local_operations_count: int = 0

class ProviderCapability(BaseModel):
    provider_name: str
    model_name: str
    input_cost_per_m: float
    output_cost_per_m: float
    cached_cost_per_m: float = 0.0
    supports_structured_json: bool = True
    supports_vision: bool = False
    context_window: int = 128000
