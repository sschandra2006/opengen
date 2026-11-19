import os
from typing import Optional, List
from .base import BaseAIProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider
from .offline_provider import OfflineDeterministicProvider

class AIProviderFactory:
    """
    Factory & Router for OpenGen AI Providers.
    Resolves providers with graceful fallback hierarchy.
    """
    SUPPORTED_PROVIDERS: List[str] = ["gemini", "openai", "anthropic", "ollama", "offline"]

    @classmethod
    def get_provider(
        cls,
        provider_name: Optional[str] = None,
        model: Optional[str] = None
    ) -> BaseAIProvider:
        ptype = provider_name or os.getenv("OPENGEN_AI_PROVIDER")

        # Automatic detection of available API keys/servers
        if not ptype:
            if os.getenv("GEMINI_API_KEY"):
                ptype = "gemini"
            elif os.getenv("OPENAI_API_KEY"):
                ptype = "openai"
            elif os.getenv("ANTHROPIC_API_KEY"):
                ptype = "anthropic"
            elif os.getenv("OLLAMA_HOST") or os.getenv("OLLAMA_MODEL"):
                ptype = "ollama"
            else:
                ptype = "offline"

        ptype = ptype.lower().strip()

        # Attempt instantiation with fallback
        try:
            if ptype == "gemini":
                return GeminiProvider(model_name=model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
        except Exception as e:
            print(f"[AIProviderFactory] Notice: Gemini provider unavailable ({e}). Falling back.")

        try:
            if ptype == "openai" or (not provider_name and os.getenv("OPENAI_API_KEY")):
                return OpenAIProvider(model_name=model or os.getenv("OPENAI_MODEL", "gpt-4o"))
        except Exception as e:
            print(f"[AIProviderFactory] Notice: OpenAI provider unavailable ({e}). Falling back.")

        try:
            if ptype == "anthropic" or (not provider_name and os.getenv("ANTHROPIC_API_KEY")):
                return AnthropicProvider(model_name=model or os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219"))
        except Exception as e:
            print(f"[AIProviderFactory] Notice: Anthropic provider unavailable ({e}). Falling back.")

        try:
            if ptype in ("ollama", "local", "vllm"):
                return OllamaProvider(
                    base_url=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434/v1"),
                    model_name=model or os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
                )
        except Exception as e:
            print(f"[AIProviderFactory] Notice: Ollama provider unavailable ({e}). Falling back.")

        # Always safe offline fallback
        return OfflineDeterministicProvider()
