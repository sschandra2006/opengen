# 10. UNIFIED PROVIDER MANAGER IMPLEMENTATION PLAN

> **Document ID:** `OPENGEN-PROV-010`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Infrastructure Engineer  
> **Project:** OpenGen Framework  
> **Date:** November 2026  
> **Subsystem:** Multi-Provider Abstraction & BYOK Management  

---

## 1. Subsystem Scope & Architectural Objectives

The `ProviderManager` is OpenGen's centralized artificial intelligence gateway. It decouples all four generation engines from specific AI vendors, delivering:

1. **Universal Model Interoperability:** A single, consistent interface wrapping Google Gemini, OpenAI, Anthropic Claude, Together AI, Fireworks AI, OpenRouter, and local Ollama.
2. **Bring Your Own Key (BYOK):** Seamless support for user-supplied API keys per request or environment-level system keys.
3. **Task-Driven Smart Routing:** Automatically directs subtasks to the most cost-effective and capable model (e.g., cheap models for JSON extraction; flagship models only when deep reasoning is explicitly requested).
4. **Provider Capability Registry:** Tracks which models support native JSON schema decoding, vision multimodal inputs, prompt caching, and tool use.
5. **Automatic Fallback Chains:** Automatically falls back across providers if a primary API encounters rate limits (429) or downtime (503).
6. **Unified Token & Cost Accounting:** Normalizes input, output, and cached tokens into exact real-time USD billing metrics.

---

## 2. Provider Abstraction Architecture (`LiteLLM` Bridge)

```mermaid
flowchart TD
    ENGINES["Generation Engines (A, B, C, D) / MCP Tools / API"] --> ROUTE["ProviderManager.complete(task_type, prompt, schema)"]
    
    ROUTE --> REGISTRY["Capability & Pricing Registry\n* Supported Features\n* Normalized Pricing / 1M tokens"]
    
    REGISTRY --> SELECT{"Task-Based Model Selection"}
    
    SELECT -->|Planning / Extraction| CHEAP["Tier 1: Economical Flash / Mini\n* gemini-2.5-flash ($0.30 in / $2.50 out)\n* gpt-4o-mini ($0.15 in / $0.60 out)\n* Together Llama-3.1-8B ($0.18 in / $0.18 out)"]
    
    SELECT -->|Offline / Zero-Cost| LOCAL["Tier 0: Local Inference\n* ollama/qwen3:8b ($0.00)\n* ollama/llama3.2:8b ($0.00)"]
    
    SELECT -->|Complex Synthesis / Ambiguity| FLAGSHIP["Tier 2: Flagship Reasoning\n* claude-3-5-sonnet\n* gpt-4o\n* gemini-2.5-pro"]
    
    CHEAP --> LITELLM["LiteLLM Universal Translation Gateway\n* Standardizes Request & Response\n* Normalizes Exceptions\n* Enforces Pydantic Schema"]
    LOCAL --> LITELLM
    FLAGSHIP --> LITELLM
    
    LITELLM --> RETRY{"API Call Success?"}
    RETRY -->|Yes| TELEMETRY["Cost & Token Normalizer\n* Calculate input, output, cached tokens\n* Compute USD cost"]
    RETRY -->|Fail (429/500/Timeout)| FALLBACK["Execute Fallback Chain\n(e.g., Gemini -> OpenAI -> Ollama)"]
    FALLBACK --> LITELLM
    
    TELEMETRY --> OUTPUT["Structured Pydantic Model + Cost Metadata"]
    OUTPUT --> ENGINES
```

---

## 3. Subsystem Specifications & Components

### 3.1 Component 1: Capability Registry (`registry.py`)
- **Target Location:** `src/opengen/providers/registry.py`.
- Maintains static and dynamic metadata for all supported AI models:

| Provider | Model Identifier | Input $/1M | Output $/1M | Cached $/1M | JSON Schema | Multimodal Vision | Context Window |
|---|---|---|---|---|---|---|---|
| **Google** | `gemini-2.5-flash` | $0.30 | $2.50 | $0.03 | Native Schema | Yes | 1,000,000 |
| **Google** | `gemini-2.5-pro` | $1.25 | $10.00 | $0.125 | Native Schema | Yes | 2,000,000 |
| **OpenAI** | `gpt-4o-mini` | $0.15 | $0.60 | $0.075 | `strict: true` | Yes | 128,000 |
| **OpenAI** | `gpt-4o` | $5.00 | $15.00 | $2.50 | `strict: true` | Yes | 128,000 |
| **Anthropic** | `claude-3-5-haiku` | $0.80 | $4.00 | $0.08 | Tool Use | Yes | 200,000 |
| **Anthropic** | `claude-3-5-sonnet` | $3.00 | $15.00 | $0.30 | Tool Use | Yes | 200,000 |
| **Together** | `together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` | $0.18 | $0.18 | N/A | Grammar/JSON | No | 128,000 |
| **Ollama** | `ollama/qwen3:8b` | $0.00 | $0.00 | $0.00 | Format: json | No | 32,000 |

---

### 3.2 Component 2: Unified Provider Interface (`manager.py`)
- **Target Location:** `src/opengen/providers/manager.py`.

```python
from typing import Type, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel
import litellm

T = TypeVar("T", bound=BaseModel)

class ProviderManager:
    """Central gateway for all LLM and Multimodal operations."""

    def __init__(self, default_model: Optional[str] = None):
        self.default_model = default_model or "gemini/gemini-2.5-flash"
        # Enable LiteLLM silent dropping of unsupported params
        litellm.drop_params = True

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str = "",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        fallbacks: Optional[List[str]] = None,
        temperature: float = 0.1
    ) -> Tuple[T, TokenCostReport]:
        target_model = model or self.default_model
        fallback_models = fallbacks or ["openai/gpt-4o-mini", "ollama/qwen3:8b"]

        try:
            response = await litellm.acompletion(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format=response_model,
                temperature=temperature,
                api_key=api_key,
                fallbacks=fallback_models
            )
            parsed_obj = response_model.model_validate_json(
                response.choices[0].message.content
            )
            cost = litellm.completion_cost(completion_response=response)
            usage = response.usage
            return parsed_obj, TokenCostReport(
                model_used=response.model,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                cost_usd=round(cost, 6)
            )
        except Exception as e:
            logger.error(f"Structured LLM generation failed across fallback chain: {e}")
            raise ProviderError(f"Model generation failed: {e}") from e
```

---

### 3.3 Component 3: Task-Based Routing Heuristics
When engines submit tasks without specifying a model, `ProviderManager.route_task(task_type)` selects the optimal model:

1. **`task_type == "preliminary_extraction"`:**
   - Preferred: Local `ollama/qwen3:8b` (0 cloud tokens) or `gemini-2.5-flash`.
2. **`task_type == "presentation_planning"`:**
   - Preferred: `gemini-2.5-flash` or `gpt-4o-mini` (fast, high JSON adherence, ~$0.001 per deck).
3. **`task_type == "conflict_resolution"`:**
   - Preferred: `gemini-2.5-flash` or `claude-3-5-haiku`.
4. **`task_type == "deep_document_synthesis"`:**
   - Preferred: `claude-3-5-sonnet` or `gemini-2.5-pro` (if requested by user).

---

### 3.4 Component 4: BYOK Security & Request Isolation
- **Request-Level Key Injection:** In REST API, MCP, and SDK calls, users can supply headers:
  - `X-OpenAI-Key: sk-...`
  - `X-Gemini-Key: AIza...`
  - `X-Anthropic-Key: sk-ant-...`
- **Security Protections:**
  1. API keys are passed directly into ephemeral LiteLLM call arguments.
  2. Keys are typed as `pydantic.SecretStr` in request DTOs.
  3. Never written to SQLite, never written to diskcache, never printed in log files.

---

## 4. Migration Plan for Existing Codebase

- **Deprecation:** The existing `app/modules/token_optimization/ai_router.py` will be safely deprecated and replaced by `src/opengen/providers/manager.py`.
- **Backward Compatibility:** All existing calls from `mapper.py` and `information_extractor.py` (`self.ai_router.route_task(...)`) will be re-pointed to `ProviderManager.generate_structured(...)`.

---
*End of Report 10.*
