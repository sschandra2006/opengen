"""
Universal Multi-Provider Manager using LiteLLM.
Standardizes structured JSON schema output across Google Gemini, OpenAI, Claude,
DeepSeek, OpenRouter, and local/uncensored Ollama/vLLM models.
Includes De-Chatter extraction, 1-turn reflection self-healing, and automatic fallback chains.
"""
import json
import logging
import re
from typing import Type, TypeVar, Optional, Tuple, List, Dict, Any
from pydantic import BaseModel, ValidationError
import json_repair
from opengen.config import settings
from opengen.domain.errors import ProviderError
from opengen.domain.provider import TokenCostReport
from opengen.providers.registry import MODEL_REGISTRY

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

NEGATIVE_AESTHETIC_INVARIANT = (
    "\nSTRICT INVARIANT: You MUST return ONLY valid JSON matching the schema.\n"
    "DO NOT include any conversational preamble, explanations, or postscripts.\n"
    "DO NOT include emojis (such as 🚀, 🔥, 💡, 🥛, 📈).\n"
)


def extract_json_payload(text: str) -> str:
    """Extracts the outermost JSON object or array, stripping markdown fences and conversational banter."""
    if not text or not text.strip():
        return "{}"
    
    cleaned = text.strip()
    
    # Strip markdown codeblock if present
    if "```" in cleaned:
        code_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if code_match:
            cleaned = code_match.group(1).strip()

    # Find outermost JSON boundaries
    start_brace = cleaned.find("{")
    start_bracket = cleaned.find("[")
    
    start = -1
    if start_brace != -1 and start_bracket != -1:
        start = min(start_brace, start_bracket)
    elif start_brace != -1:
        start = start_brace
    elif start_bracket != -1:
        start = start_bracket

    if start != -1:
        end_brace = cleaned.rfind("}")
        end_bracket = cleaned.rfind("]")
        end = max(end_brace, end_bracket)
        if end > start:
            return cleaned[start:end + 1]

    return cleaned


class ProviderManager:
    """Central gateway for all LLM inference operations across frontier, open-weight, and uncensored models."""

    def __init__(
        self,
        default_model: Optional[str] = None,
        api_key: Optional[str] = None,
        cost_tracker: Optional[Any] = None,
    ):
        self._explicit_default_model = default_model
        self.api_key = api_key
        self.cost_tracker = cost_tracker

    @property
    def default_model(self) -> str:
        return self._explicit_default_model or settings.DEFAULT_PRIMARY_MODEL or settings.DEFAULT_LLM_MODEL

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
        Executes structured generation using LiteLLM with 1-turn reflection self-healing and fallback cascade.
        """
        target_model = model or self.default_model
        effective_key = api_key or self.api_key
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
                    api_key=effective_key,
                    temperature=temperature
                )
                if self.cost_tracker is not None:
                    self.cost_tracker.add_report(cost_report)
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
        full_system = f"{system_prompt}\nTarget JSON Schema:\n{schema_json}{NEGATIVE_AESTHETIC_INVARIANT}"

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "timeout": 90
        }

        # Resolve API keys & base URLs across providers
        if api_key:
            kwargs["api_key"] = api_key
        elif "gemini" in model and settings.GEMINI_API_KEY:
            kwargs["api_key"] = settings.GEMINI_API_KEY
        elif "openai" in model and settings.OPENAI_API_KEY:
            kwargs["api_key"] = settings.OPENAI_API_KEY
        elif "anthropic" in model and settings.ANTHROPIC_API_KEY:
            kwargs["api_key"] = settings.ANTHROPIC_API_KEY
        elif "deepseek" in model and settings.DEEPSEEK_API_KEY:
            kwargs["api_key"] = settings.DEEPSEEK_API_KEY
        elif "openrouter" in model and settings.OPENROUTER_API_KEY:
            kwargs["api_key"] = settings.OPENROUTER_API_KEY
        elif "together" in model and settings.TOGETHER_API_KEY:
            kwargs["api_key"] = settings.TOGETHER_API_KEY
        elif "ollama" in model:
            kwargs["api_base"] = settings.OLLAMA_BASE_URL
        elif "vllm" in model:
            kwargs["api_base"] = settings.VLLM_BASE_URL
        elif "local" in model:
            kwargs["api_base"] = settings.LOCAL_LLM_BASE_URL

        # Request completion
        response = litellm.completion(**kwargs)
        raw_text = response.choices[0].message.content or "{}"

        # Clean extraction
        clean_json_str = extract_json_payload(raw_text)

        # Parse JSON
        try:
            parsed_dict = json.loads(clean_json_str)
        except Exception:
            parsed_dict = json_repair.loads(clean_json_str)

        # Validate with 1-turn reflection self-healing if needed
        try:
            validated_model = response_model.model_validate(parsed_dict)
        except ValidationError as val_err:
            logger.info(f"Model '{model}' produced schema validation error: {val_err}. Triggering 1-turn reflection self-healing...")
            repair_kwargs = dict(kwargs)
            repair_kwargs["messages"] = list(kwargs["messages"]) + [
                {"role": "assistant", "content": clean_json_str},
                {
                    "role": "user",
                    "content": (
                        f"Your previous JSON output failed schema validation:\n{val_err}\n"
                        f"Correct the fields according to the schema and return ONLY the valid JSON."
                    )
                }
            ]
            repair_resp = litellm.completion(**repair_kwargs)
            repair_text = repair_resp.choices[0].message.content or "{}"
            repaired_json = extract_json_payload(repair_text)
            try:
                repaired_dict = json.loads(repaired_json)
            except Exception:
                repaired_dict = json_repair.loads(repaired_json)
            validated_model = response_model.model_validate(repaired_dict)

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
