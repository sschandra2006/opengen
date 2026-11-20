"""
Provider capability and pricing registry.
Normalizes rates per 1 Million tokens and model feature support.
Supports Frontier, Open-Weight, Uncensored, and Local Inference.
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
    "anthropic/claude-3-7-sonnet": ProviderCapability(
        provider_name="anthropic",
        model_name="claude-3-7-sonnet",
        input_cost_per_m=3.00,
        output_cost_per_m=15.00,
        cached_cost_per_m=0.30,
        supports_structured_json=True,
        supports_vision=True,
        context_window=200000
    ),

    # DeepSeek Models
    "deepseek/deepseek-chat": ProviderCapability(
        provider_name="deepseek",
        model_name="deepseek-v3",
        input_cost_per_m=0.27,
        output_cost_per_m=1.10,
        cached_cost_per_m=0.07,
        supports_structured_json=True,
        supports_vision=False,
        context_window=64000
    ),
    "deepseek/deepseek-reasoner": ProviderCapability(
        provider_name="deepseek",
        model_name="deepseek-r1",
        input_cost_per_m=0.55,
        output_cost_per_m=2.19,
        cached_cost_per_m=0.14,
        supports_structured_json=True,
        supports_vision=False,
        context_window=64000
    ),

    # Open-Weight / Together AI / Groq
    "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo": ProviderCapability(
        provider_name="together",
        model_name="Llama-3.3-70B-Instruct-Turbo",
        input_cost_per_m=0.88,
        output_cost_per_m=0.88,
        cached_cost_per_m=0.0,
        supports_structured_json=True,
        supports_vision=False,
        context_window=128000
    ),
    "together_ai/Qwen/Qwen2.5-Coder-32B-Instruct": ProviderCapability(
        provider_name="together",
        model_name="Qwen2.5-Coder-32B-Instruct",
        input_cost_per_m=0.80,
        output_cost_per_m=0.80,
        cached_cost_per_m=0.0,
        supports_structured_json=True,
        supports_vision=False,
        context_window=128000
    ),

    # Local Ollama & Uncensored Models (Zero Cost)
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
    ),
    "ollama/dolphin-llama3:8b": ProviderCapability(
        provider_name="ollama",
        model_name="dolphin-llama3:8b",
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        cached_cost_per_m=0.0,
        supports_structured_json=True,
        supports_vision=False,
        context_window=32000
    ),
    "ollama/hermes3:8b": ProviderCapability(
        provider_name="ollama",
        model_name="hermes3:8b",
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        cached_cost_per_m=0.0,
        supports_structured_json=True,
        supports_vision=False,
        context_window=32000
    ),
    "ollama/qwen2.5-coder:32b": ProviderCapability(
        provider_name="ollama",
        model_name="qwen2.5-coder:32b",
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        cached_cost_per_m=0.0,
        supports_structured_json=True,
        supports_vision=False,
        context_window=32000
    ),

    # Custom Local / vLLM / LM Studio Endpoints
    "local/custom-model": ProviderCapability(
        provider_name="local",
        model_name="custom-model",
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        cached_cost_per_m=0.0,
        supports_structured_json=True,
        supports_vision=False,
        context_window=32000
    )
}
