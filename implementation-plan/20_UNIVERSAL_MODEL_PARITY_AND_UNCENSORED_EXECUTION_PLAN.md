# 20. UNIVERSAL MODEL PARITY & UNCENSORED MODEL EXECUTION PLAN

> **Document ID:** `OPENGEN-PARITY-020`  
> **Subsystem:** AI Provider Switchboard, Model Agnostic Decoding & Creative Parity  
> **Target Module:** `src/opengen/providers/`  
> **Author:** Principal Software Architect, Senior Full-Stack Engineer, AI Framework Specialist  
> **Status:** APPROVED FOR PRODUCTION  

---

## 1. Architectural Scope

This plan specifies the technical execution required to achieve **Frontier Model Parity (Claude 3.5/3.7 Sonnet & GPT-4o quality)** when running **any open-weight, uncensored, or local model** across all 5 OpenGen studios:
- **Engine 1:** Document Studio (Typst Vector Publications)
- **Engine 2:** Presentation Studio (Responsive 12-Column Bento Decks)
- **Engine 3:** Image Studio (Studio Product Photography & Contact Shadows)
- **Engine 4:** Handwriting Studio (Biomechanical Bézier Splines & Pen Physics)
- **Engine 5:** Motion Graphics Studio (5-Phase Retention Short-Form Video Ads)

---

## 2. Technical Capabilities Added

1. **Uncensored Model De-Chatter & Markdown Isolation:**
   - Strips conversational preambles (`"Sure! Here is your JSON:"`, `"Hope this helps!"`) and extracts clean JSON from code blocks.
2. **Autonomous 1-Turn Reflection & Self-Healing Loop:**
   - Catches Pydantic validation errors and re-prompts the model with the exact field error and snippet.
3. **Dynamic Few-Shot Exemplar Injection:**
   - Detects model tier and injects 1–2 gold-standard input-output exemplars for Tier 0 (Local/Ollama) and Tier 1 (Small/Uncensored) models.
4. **Expanded Model Registry:**
   - Full support for DeepSeek-R1/V3, Qwen-2.5-Coder (7B/32B/72B), Llama-3.3-70B, Dolphin-2.9-Llama3, Hermes-3, OpenRouter, and local OpenAI-compatible endpoints (vLLM, LM Studio, Jan).
5. **Universal Negative Aesthetic Directives:**
   - Injects negative prompt constraints banning emojis, spreadsheet tables, all-caps text, and bullet-point dumps.

---

## 3. Implementation Verification Commands

```powershell
# Run the complete OpenGen test suite
cd "F:\document generator\opengen"
uv run pytest tests/ -v

# Run the creative quality gate tests specifically
uv run pytest tests/test_unified_creative_gate.py tests/test_creative_intelligence.py -v
```
