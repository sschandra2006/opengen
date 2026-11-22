"""
AI Router for local Ollama (Qwen 2.5 7B) and Cloud LLM Providers (LiteLLM, Gemini, Claude, OpenAI, DeepSeek).
Enforces the Universal Token-Reduction Architecture (UTRA):
- Zero-Chatter Directive & Negative Aesthetic constraints
- Dense Semantic DSL (Pipe/TSV delimited streams) with CPU expansion
- Early-exit stop sequences (no runaway generation)
- Deterministic 1-Turn Surgical Reflection on failed lines
- Structured JSON with GBNF grammar constraints
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List, Union
import json_repair

from app.config import settings
from app.modules.token_optimization.tracker import TokenTracker
from app.modules.token_optimization.dense_parser import (
    CatalogItem,
    DenseParseResult,
    parse_dense_items,
    parse_dense_items_with_telemetry,
    calculate_token_savings
)

logger = logging.getLogger(__name__)

ZERO_CHATTER_DIRECTIVE = (
    "\n[SYSTEM INSTRUCTION - ZERO-CHATTER DIRECTIVE]\n"
    "You are a pure data transformation engine for OpenGen.\n"
    "CRITICAL CONSTRAINTS:\n"
    "1. Output ONLY the raw records or valid JSON without any conversational text.\n"
    "2. Never include apologies, introductions, explanations, or sign-offs.\n"
    "3. Never enclose output in markdown code blocks (no ``` or ```json).\n"
    "4. Terminate generation immediately after the final record.\n"
)


class AIRouter:
    def __init__(self, tracker: Optional[TokenTracker] = None):
        self.tracker = tracker or TokenTracker()
        self.gemini_client = None
        self._init_gemini()

    def _init_gemini(self):
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel(settings.GEMINI_MODEL)
                logger.info(f"Gemini API configured with model: {settings.GEMINI_MODEL}")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini API: {e}")

    def call_ollama(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        format_json: bool = True,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Executes a local inference on Ollama with Qwen 2.5 7B.
        Applies Zero-Chatter directive, GBNF grammar masking, and early-exit stop strings.
        Cost: 0 cloud tokens.
        """
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        full_system = f"{system_prompt}{ZERO_CHATTER_DIRECTIVE}".strip()
        if format_json:
            full_system += "\nYou MUST respond ONLY with valid JSON."

        payload: Dict[str, Any] = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "system": full_system,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 1.0,
                "stop": getattr(settings, "MAX_STREAM_STOP_TOKENS", ["\n\n\n", "```", "<|im_end|>", "<|endoftext|>"]),
                "num_predict": max_tokens
            }
        }
        if format_json:
            payload["format"] = "json"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
                raw_response = result.get("response", "{}")
                prompt_eval_count = result.get("prompt_eval_count", len(prompt.split()) * 2)
                eval_count = result.get("eval_count", len(raw_response.split()) * 2)

                self.tracker.record_local_llm(prompt_eval_count + eval_count)

                if not format_json:
                    return {"raw_text": raw_response}

                # Parse JSON safely
                try:
                    return json.loads(raw_response)
                except Exception:
                    return json_repair.loads(raw_response)
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            return {}

    def call_gemini(self, prompt: str, system_prompt: str = "", stage: str = "general") -> Dict[str, Any]:
        """Legacy method for cloud generation. Redirects to call_cloud."""
        return self.call_cloud(prompt, system_prompt, stage=stage)

    def call_cloud(
        self,
        prompt: str,
        system_prompt: str = "",
        stage: str = "general",
        temperature: float = 0.0,
        format_json: bool = True
    ) -> Dict[str, Any]:
        """
        Universal cloud LLM inference gateway across OpenAI, Anthropic, DeepSeek, Gemini, and OpenRouter.
        Applies Zero-Chatter directive and early stop tokens. Falls back to local Ollama if offline.
        """
        full_system = f"{system_prompt}{ZERO_CHATTER_DIRECTIVE}".strip()

        # Try universal LiteLLM first
        try:
            import litellm
            from opengen.config import resolve_default_model
            model = resolve_default_model()
            if not model.startswith("ollama/"):
                messages = []
                if full_system:
                    messages.append({"role": "system", "content": full_system})
                messages.append({"role": "user", "content": prompt})

                kwargs: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "stop": getattr(settings, "MAX_STREAM_STOP_TOKENS", ["\n\n\n", "```", "<|im_end|>"])
                }
                if format_json:
                    kwargs["response_format"] = {"type": "json_object"}

                resp = litellm.completion(**kwargs)
                raw_text = resp.choices[0].message.content or "{}"
                in_tok = getattr(resp.usage, "prompt_tokens", len(prompt.split()) * 2)
                out_tok = getattr(resp.usage, "completion_tokens", len(raw_text.split()) * 2)
                self.tracker.record_gemini(stage, in_tok, out_tok)

                if not format_json:
                    return {"raw_text": raw_text}

                try:
                    return json.loads(raw_text)
                except Exception:
                    return json_repair.loads(raw_text)
        except Exception as ex:
            logger.debug(f"LiteLLM call in AIRouter skipped or failed: {ex}")

        # Fallback to direct Gemini SDK if configured
        if not self.gemini_client:
            logger.info("No cloud API keys configured. Routing call to local Qwen 2.5 7B.")
            return self.call_ollama(prompt, system_prompt, temperature=temperature, format_json=format_json)

        full_prompt = f"{full_system}\n\nTask:\n{prompt}"
        try:
            gen_config: Dict[str, Any] = {
                "temperature": temperature,
                "stop_sequences": ["\n\n\n", "```", "<|im_end|>"]
            }
            if format_json:
                gen_config["response_mime_type"] = "application/json"

            response = self.gemini_client.generate_content(
                full_prompt,
                generation_config=gen_config
            )
            raw_text = response.text or "{}"

            input_tokens = len(full_prompt.split()) * 2
            output_tokens = len(raw_text.split()) * 2
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                input_tokens = getattr(response.usage_metadata, "prompt_token_count", input_tokens)
                output_tokens = getattr(response.usage_metadata, "candidates_token_count", output_tokens)

            self.tracker.record_gemini(stage, input_tokens, output_tokens)

            if not format_json:
                return {"raw_text": raw_text}

            try:
                return json.loads(raw_text)
            except Exception:
                return json_repair.loads(raw_text)
        except Exception as e:
            logger.warning(f"Cloud API call failed ({e}). Falling back to local Qwen 2.5 7B.")
            return self.call_ollama(prompt, system_prompt, temperature=temperature, format_json=format_json)

    def call_dense_dsl(
        self,
        prompt: str,
        system_prompt: str = "",
        delimiter: str = "|",
        stage: str = "dense_catalog_extraction",
        use_surgical_reflection: bool = True
    ) -> List[CatalogItem]:
        """
        Universal Dense Semantic DSL generation gateway (Mechanism 1 & 4 of UTRA).
        Produces raw pipe-delimited records instead of bloated JSON (saves 65%–80% tokens).
        If any individual line is malformed, performs surgical 1-turn reflection on that line only.
        """
        dense_prompt = (
            f"{prompt}\n\n"
            f"OUTPUT FORMAT REQUIREMENT:\n"
            f"Output strictly one record per line using delimiter '{delimiter}':\n"
            f"SKU{delimiter}NAME{delimiter}CATEGORY{delimiter}MRP{delimiter}PRICE[|UNIT|IS_HERO]\n"
            f"No header row, no markdown fences, no conversational text."
        )

        # Call local or cloud with format_json=False
        res = self.call_cloud(dense_prompt, system_prompt, stage=stage, temperature=0.0, format_json=False)
        raw_text = res.get("raw_text", "")
        if not raw_text:
            raw_text = self.call_ollama(dense_prompt, system_prompt, temperature=0.0, format_json=False).get("raw_text", "")

        # Parse with telemetry
        parsed = parse_dense_items_with_telemetry(raw_text, delimiter=delimiter)
        items = list(parsed.items)

        # Surgical 1-Turn Reflection (Mechanism 4)
        if use_surgical_reflection and parsed.malformed_lines:
            logger.info(f"Dense parser detected {len(parsed.malformed_lines)} malformed lines. Triggering surgical 1-turn reflection...")
            for line_no, raw_line, reason in parsed.malformed_lines:
                repair_prompt = (
                    f"The following line failed schema validation:\n'{raw_line}'\n"
                    f"Reason: {reason}\n"
                    f"Format: SKU{delimiter}NAME{delimiter}CATEGORY{delimiter}MRP{delimiter}PRICE[|UNIT|IS_HERO]\n"
                    f"Output ONLY the corrected single line without code blocks or chatter."
                )
                repair_res = self.call_cloud(repair_prompt, system_prompt="", stage="surgical_reflection", temperature=0.0, format_json=False)
                repaired_text = repair_res.get("raw_text", "").strip()
                if repaired_text:
                    repaired_items = parse_dense_items(repaired_text, delimiter=delimiter)
                    if repaired_items:
                        items.append(repaired_items[0])

        return items

    def route_task(self, task_type: str, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """
        Smart routing according to Module 8:
        - basic classification / simple extraction -> Qwen 2.5 7B (Local)
        - complex semantic reasoning / conflict resolution -> Cloud Models (Gemini, Claude, GPT, DeepSeek)
        """
        if task_type in ["classification", "preliminary_extraction", "basic_mapping", "summarization"]:
            return self.call_ollama(prompt, system_prompt)
        else:
            return self.call_cloud(prompt, system_prompt, stage=task_type)
