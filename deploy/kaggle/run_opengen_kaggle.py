#!/usr/bin/env python3
"""
OpenGen Kaggle Deployment Runner with Cloudflare Tunnel.
Launches the OpenGen FastAPI backend on port 8000 and exposes a public URL via cloudflared.
Zero configuration required on Kaggle free notebook sessions.
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


def start_tunnel(port: int = 8000):
    """Spawns cloudflared tunnel and logs the assigned public URL."""
    cf_path = install_cloudflared()
    logger.info(f"Starting Cloudflare tunnel on port {port}...")
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
                        logger.info(f"\n{'='*70}\n[OPENGEN LIVE PUBLIC ENDPOINT]: {word}\n{'='*70}\n")
                        break

    threading.Thread(target=monitor_tunnel, args=(proc.stderr,), daemon=True).start()
    return proc


def run_server(port: int = 8000):
    """Starts OpenGen backend via Uvicorn."""
    import uvicorn
    os.environ["OLLAMA_MODEL"] = os.environ.get("OLLAMA_MODEL", "opengen-qwen")
    os.environ["OPENGEN_DEFAULT_PRIMARY_MODEL"] = "ollama/opengen-qwen"

    logger.info(f"Starting OpenGen API on port {port}...")
    start_tunnel(port)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    run_server(port)
