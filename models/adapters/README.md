# OpenGen LoRA Adapters Directory

This directory stores lightweight LoRA adapter checkpoints (typically ~25MB) produced by OpenGen fine-tuning workflows (e.g. `scripts/train_opengen_qwen.py`).

## Weight Storage Architectural Principles
As documented in `OPENGEN_UNIVERSAL_TOKEN_REDUCTION_AND_MODEL_OPTIMIZATION_REPORT.md` (Part C):

1. **NEVER commit raw model weights (>50MB):** Base transformer weights (e.g. 5GB–15GB `.safetensors` or `.gguf` files) must NEVER be committed to this repository.
2. **Commit Only Small PEFT/LoRA Adapters:** Only lightweight adapter parameter deltas (`adapter_model.safetensors`, `adapter_config.json`) under 30MB may reside here.
3. **External Model Weight Workflows:**
   - **Kaggle Instant Mount:** Use Kaggle's `/kaggle/input/qwen-2.5-7b-instruct/` (0 MB disk used in `/kaggle/working`).
   - **Ollama Pull:** Use `ollama run qwen2.5:7b` (stored in Ollama system blob storage outside the project repo).
   - **HuggingFace Hub Cache:** Cached in `~/.cache/huggingface/` outside the project repository.
