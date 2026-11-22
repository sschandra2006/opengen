#!/bin/bash
# ==============================================================================
# OpenGen Kaggle Free-Tier Runtime Setup Script (Tesla T4 / P100 16GB VRAM)
# Respects Kaggle's 20GB /kaggle/working disk quota:
# - Mounts Qwen 2.5 7B from Kaggle Models input (0 MB disk space used)
# - Installs Ollama into /tmp or runs direct vLLM/llama.cpp
# - Launches background serving daemon
# ==============================================================================

set -e

echo "[OpenGen] Initializing Kaggle Free Tier Environment..."

# 1. Verify GPU availability
if command -v nvidia-smi &> /dev/null; then
    echo "[OpenGen] GPU Detected:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
else
    echo "[OpenGen] WARNING: No NVIDIA GPU detected. Running in CPU mode."
fi

# 2. Install Ollama into /tmp (avoids consuming /kaggle/working quota)
export OLLAMA_MODELS="/tmp/ollama_models"
mkdir -p "$OLLAMA_MODELS"

if ! command -v ollama &> /dev/null; then
    echo "[OpenGen] Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# 3. Start Ollama in background
echo "[OpenGen] Starting Ollama daemon on port 11434..."
ollama serve > /tmp/ollama.log 2>&1 &
sleep 4

# 4. Check for Kaggle Mounted Model or Pull Uncensored Abliterated Qwen 2.5 7B
KAGGLE_MODEL_INPUT="/kaggle/input/qwen-2.5-7b-instruct"
KAGGLE_UNCENSORED_INPUT="/kaggle/input/qwen-2-5-7b-instruct-abliterated"
if [ -d "$KAGGLE_UNCENSORED_INPUT" ]; then
    echo "[OpenGen] Found Kaggle Uncensored Model Mount at $KAGGLE_UNCENSORED_INPUT (0 MB disk used)"
elif [ -d "$KAGGLE_MODEL_INPUT" ]; then
    echo "[OpenGen] Found Kaggle Model Mount at $KAGGLE_MODEL_INPUT (0 MB disk used)"
else
    echo "[OpenGen] Pulling huihui_ai/qwen2.5-abliterated:7b into /tmp..."
    ollama pull huihui_ai/qwen2.5-abliterated:7b
fi

# 5. Build OpenGen Optimized Model
if [ -f "deploy/ollama/Modelfile.opengen_qwen" ]; then
    echo "[OpenGen] Creating opengen-qwen optimized model..."
    ollama create opengen-qwen -f deploy/ollama/Modelfile.opengen_qwen
fi

echo "[OpenGen] Environment ready! You can now run deploy/kaggle/run_opengen_kaggle.py"
