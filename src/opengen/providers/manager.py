"""
Universal Multi-Provider Manager using LiteLLM.
Standardizes structured JSON schema output across Google Gemini, OpenAI, Claude, and local Ollama.
Supports per-request BYOK and automatic fallback chains.
"""
import json
import logging
from typing import Type, TypeVar, Optional, Tuple, List, Dict, Any
from pydantic import BaseModel
import json_repair
from opengen.config import settings
from opengen.domain.errors import ProviderError
from opengen.domain.provider import TokenCostReport
from opengen.providers.registry import MODEL_REGISTRY

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

class ProviderManager:
    """Central gateway for all LLM inference operations."""

    def __init__(self, default_model: Optional[str] = None):
        self.default_model = default_model or settings.DEFAULT_LLM_MODEL

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str = "You are a professional generation assistant. Respond strictly with valid JSON conforming to the schema.",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        fallbacks: Optional[List[str]] = None,
        temperature: float = 0.1
    ) -> Tuple[T, TokenCostReport]:
        """
        Executes structured generation using LiteLLM with fallback cascade.
        """
        target_model = model or self.default_model
        fallback_chain = fallbacks or [settings.DEFAULT_FAST_MODEL, settings.DEFAULT_LOCAL_MODEL]
        models_to_try = [target_model] + [f for f in fallback_chain if f != target_model]

        last_error = None
        for m in models_to_try:
            try:
                result_obj, cost_report = self._call_model(
                    model=m,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    response_model=response_model,
                    api_key=api_key,
                    temperature=temperature
                )
                return result_obj, cost_report
            except Exception as e:
                logger.warning(f"Provider model '{m}' call failed: {e}. Trying fallback...")
                last_error = e

        raise ProviderError(f"All configured provider models failed. Last error: {last_error}")

    def _call_model(
        self,
        model: str,
        prompt: str,
        system_prompt: str,
        response_model: Type[T],
        api_key: Optional[str],
        temperature: float
    ) -> Tuple[T, TokenCostReport]:
        import litellm
        litellm.drop_params = True

        schema_json = json.dumps(response_model.model_json_schema())
        full_system = f"{system_prompt}\nTarget JSON Schema:\n{schema_json}\nYou MUST return ONLY valid JSON."

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "timeout": 90
        }

        # Resolve API keys
        if api_key:
            kwargs["api_key"] = api_key
        elif "gemini" in model and settings.GEMINI_API_KEY:
            kwargs["api_key"] = settings.GEMINI_API_KEY
        elif "openai" in model and settings.OPENAI_API_KEY:
            kwargs["api_key"] = settings.OPENAI_API_KEY
        elif "anthropic" in model and settings.ANTHROPIC_API_KEY:
            kwargs["api_key"] = settings.ANTHROPIC_API_KEY
        elif "ollama" in model:
            kwargs["api_base"] = settings.OLLAMA_BASE_URL

        # Request completion
        response = litellm.completion(**kwargs)
        raw_text = response.choices[0].message.content or "{}"

        # Parse JSON cleanly
        try:
            parsed_dict = json.loads(raw_text)
        except Exception:
            parsed_dict = json_repair.loads(raw_text)

        validated_model = response_model.model_validate(parsed_dict)

        # Telemetry
        usage = getattr(response, "usage", None)
        in_tokens = getattr(usage, "prompt_tokens", len(prompt.split()) * 2) if usage else 0
        out_tokens = getattr(usage, "completion_tokens", len(raw_text.split()) * 2) if usage else 0

        cap = MODEL_REGISTRY.get(model)
        rate_in = cap.input_cost_per_m if cap else 0.30
        rate_out = cap.output_cost_per_m if cap else 2.50
        cost_usd = round(((in_tokens / 1_000_000.0) * rate_in) + ((out_tokens / 1_000_000.0) * rate_out), 6)

        return validated_model, TokenCostReport(
            model_used=model,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            cost_usd=cost_usd
        )

provider_manager = ProviderManager()
