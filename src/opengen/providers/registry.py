"""
Provider capability and pricing registry.
Normalizes rates per 1 Million tokens and model feature support.
"""
from typing import Dict
from opengen.domain.provider import ProviderCapability

MODEL_REGISTRY: Dict[str, ProviderCapability] = {
    # Google Gemini Models
    "gemini/gemini-2.5-flash": ProviderCapability(
        provider_name="google",
        model_name="gemini-2.5-flash",
        input_cost_per_m=0.30,
        output_cost_per_m=2.50,
        cached_cost_per_m=0.03,
        supports_structured_json=True,
        supports_vision=True,
        context_window=1000000
    ),
    "gemini/gemini-2.5-pro": ProviderCapability(
        provider_name="google",
        model_name="gemini-2.5-pro",
        input_cost_per_m=1.25,
        output_cost_per_m=10.00,
        cached_cost_per_m=0.125,
        supports_structured_json=True,
        supports_vision=True,
        context_window=2000000
    ),

    # OpenAI Models
    "openai/gpt-4o-mini": ProviderCapability(
        provider_name="openai",
        model_name="gpt-4o-mini",
        input_cost_per_m=0.15,
        output_cost_per_m=0.60,
        cached_cost_per_m=0.075,
        supports_structured_json=True,
        supports_vision=True,
        context_window=128000
    ),
    "openai/gpt-4o": ProviderCapability(
        provider_name="openai",
        model_name="gpt-4o",
        input_cost_per_m=5.00,
        output_cost_per_m=15.00,
        cached_cost_per_m=2.50,
        supports_structured_json=True,
        supports_vision=True,
        context_window=128000
    ),

    # Anthropic Claude Models
    "anthropic/claude-3-5-haiku-20241022": ProviderCapability(
        provider_name="anthropic",
        model_name="claude-3-5-haiku",
        input_cost_per_m=0.80,
        output_cost_per_m=4.00,
        cached_cost_per_m=0.08,
        supports_structured_json=True,
        supports_vision=True,
        context_window=200000
    ),
    "anthropic/claude-3-5-sonnet-20241022": ProviderCapability(
        provider_name="anthropic",
        model_name="claude-3-5-sonnet",
        input_cost_per_m=3.00,
        output_cost_per_m=15.00,
        cached_cost_per_m=0.30,
        supports_structured_json=True,
        supports_vision=True,
        context_window=200000
    ),

    # Local Ollama Models (Zero Cost)
    "ollama/qwen3:8b": ProviderCapability(
        provider_name="ollama",
        model_name="qwen3:8b",
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        cached_cost_per_m=0.0,
        supports_structured_json=True,
        supports_vision=False,
        context_window=32000
    ),
    "ollama/llama3.2:8b": ProviderCapability(
        provider_name="ollama",
        model_name="llama3.2:8b",
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        cached_cost_per_m=0.0,
        supports_structured_json=True,
        supports_vision=False,
        context_window=32000
    )
}
