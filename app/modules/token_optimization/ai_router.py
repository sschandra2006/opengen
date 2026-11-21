"""
AI Router for local Ollama (Qwen3:8B) and Cloud Google Gemini Flash API.
Enforces structured JSON outputs, fallback mechanisms, and token tracking.
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Union
import json_repair

from app.config import settings
from app.modules.token_optimization.tracker import TokenTracker

logger = logging.getLogger(__name__)

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

    def call_ollama(self, prompt: str, system_prompt: str = "", temperature: float = 0.1) -> Dict[str, Any]:
        """
        Executes a local inference on Ollama with Qwen3:8B and structured JSON response.
        Cost: 0 cloud tokens.
        """
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "system": system_prompt + "\nYou MUST respond ONLY with valid JSON. Do not include markdown codeblocks or conversational text.",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": 512
            }
        }
        
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

    def call_cloud(self, prompt: str, system_prompt: str = "", stage: str = "general") -> Dict[str, Any]:
        """
        Universal cloud LLM inference gateway across OpenAI, Anthropic, DeepSeek, Gemini, and OpenRouter.
        Falls back to local Ollama if cloud is unavailable or keys missing.
        """
        # Try universal LiteLLM first
        try:
            import litellm
            from opengen.config import resolve_default_model
            model = resolve_default_model()
            if not model.startswith("ollama/"):
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt + "\nRespond strictly in valid JSON."})
                messages.append({"role": "user", "content": prompt})

                resp = litellm.completion(
                    model=model,
                    messages=messages,
                    temperature=0.1
                )
                raw_text = resp.choices[0].message.content or "{}"
                in_tok = getattr(resp.usage, "prompt_tokens", len(prompt.split()) * 2)
                out_tok = getattr(resp.usage, "completion_tokens", len(raw_text.split()) * 2)
                self.tracker.record_gemini(stage, in_tok, out_tok)
                try:
                    return json.loads(raw_text)
                except Exception:
                    return json_repair.loads(raw_text)
        except Exception as ex:
            logger.debug(f"LiteLLM call in AIRouter skipped or failed: {ex}")

        # Fallback to direct Gemini SDK if configured
        if not self.gemini_client:
            logger.info("No cloud API keys configured. Routing call to local Qwen3:8B.")
            return self.call_ollama(prompt, system_prompt)

        full_prompt = f"{system_prompt}\n\nTask:\n{prompt}\n\nRespond strictly with valid JSON."
        try:
            response = self.gemini_client.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_text = response.text or "{}"
            
            # Approximate or extract token usage
            input_tokens = len(full_prompt.split()) * 2
            output_tokens = len(raw_text.split()) * 2
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                input_tokens = getattr(response.usage_metadata, "prompt_token_count", input_tokens)
                output_tokens = getattr(response.usage_metadata, "candidates_token_count", output_tokens)

            self.tracker.record_gemini(stage, input_tokens, output_tokens)

            try:
                return json.loads(raw_text)
            except Exception:
                return json_repair.loads(raw_text)
        except Exception as e:
            logger.warning(f"Cloud API call failed ({e}). Falling back to local Qwen3:8B.")
            return self.call_ollama(prompt, system_prompt)

    def route_task(self, task_type: str, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """
        Smart routing according to Module 8:
        - basic classification / simple extraction -> Qwen3:8B (Local)
        - complex semantic reasoning / conflict resolution -> Cloud Models (Gemini, Claude, GPT, DeepSeek)
        """
        if task_type in ["classification", "preliminary_extraction", "basic_mapping", "summarization"]:
            return self.call_ollama(prompt, system_prompt)
        else:
            return self.call_cloud(prompt, system_prompt, stage=task_type)
