#!/usr/bin/env python3
"""
OpenGen Kaggle Uncensored Model Server.
Runs ONLY the optimized, uncensored Qwen 2.5 7B model on Kaggle's free GPU (Tesla T4)
and exposes port 11434 directly via Cloudflare Tunnel so you can run the entire
OpenGen module locally on your laptop with 0 GPU load on your laptop.
"""
import os
import sys
import time
import subprocess
import threading
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def install_cloudflared():
    """Downloads cloudflared binary to /tmp if not already present."""
    cf_path = "/tmp/cloudflared"
    if not os.path.exists(cf_path):
        logger.info("Downloading cloudflared binary to /tmp...")
        cmd = "curl -L --output /tmp/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x /tmp/cloudflared"
        subprocess.run(cmd, shell=True, check=True)
    return cf_path


def start_ollama_and_tunnel(port: int = 11434):
    """Installs Ollama in /tmp, pulls uncensored model, and tunnels port 11434."""
    # 1. Setup Ollama storage in /tmp
    os.environ["OLLAMA_MODELS"] = "/tmp/ollama_models"
    os.makedirs("/tmp/ollama_models", exist_ok=True)

    # 2. Start Ollama daemon
    logger.info("Starting Ollama daemon in background...")
    subprocess.Popen(["ollama", "serve"], env=dict(os.environ, OLLAMA_MODELS="/tmp/ollama_models"))
    time.sleep(5)

    # 3. Pull uncensored abliterated model
    logger.info("Pulling huihui_ai/qwen2.5-abliterated:7b into /tmp...")
    subprocess.run(["ollama", "pull", "huihui_ai/qwen2.5-abliterated:7b"], check=True)

    # 4. Create optimized zero-chatter model
    modelfile_path = "deploy/ollama/Modelfile.opengen_qwen"
    if os.path.exists(modelfile_path):
        logger.info(f"Applying zero-chatter Modelfile from {modelfile_path}...")
        subprocess.run(["ollama", "create", "opengen-uncensored", "-f", modelfile_path], check=True)

    # 5. Start Cloudflare tunnel directly to Ollama port 11434
    cf_path = install_cloudflared()
    logger.info(f"Starting Cloudflare tunnel to Ollama port {port}...")
    proc = subprocess.Popen(
        [cf_path, "tunnel", "--url", f"http://127.0.0.1:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    def monitor_tunnel(pipe):
        for line in pipe:
            if "trycloudflare.com" in line:
                for word in line.split():
                    if "trycloudflare.com" in word:
                        logger.info(f"\n{'='*75}\n[KAGGLE UNCENSORED MODEL ENDPOINT READY]:\n{word}\n\nSet this in your laptop's .env file:\nOLLAMA_BASE_URL={word}\nOLLAMA_MODEL=opengen-uncensored\n{'='*75}\n")
                        break

    threading.Thread(target=monitor_tunnel, args=(proc.stderr,), daemon=True).start()

    # Keep alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down model tunnel.")


if __name__ == "__main__":
    start_ollama_and_tunnel()
