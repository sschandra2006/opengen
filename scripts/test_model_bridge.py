"""
OpenGen Model Bridge Diagnostic Tool.
Tests connectivity between your laptop's OpenGen engine and the uncensored model
running on Kaggle (or local Ollama).
"""
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.modules.token_optimization.ai_router import AIRouter


def test_bridge(target_url: str = None):
    url = target_url or settings.OLLAMA_BASE_URL
    model = getattr(settings, "OLLAMA_MODEL", "opengen-uncensored")

    print("=" * 70)
    print("OPENGEN MODEL BRIDGE DIAGNOSTIC")
    print(f"Target URL: {url}")
    print(f"Target Model: {model}")
    print("=" * 70)

    # 1. Test HTTP connectivity
    import urllib.request
    import json

    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(f"{url.rstrip('/')}/api/tags", headers={"User-Agent": "OpenGen-Bridge"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            elapsed_ping = (time.perf_counter() - t0) * 1000
            print(f"[OK] HTTP Ping Succeeded in {elapsed_ping:.1f}ms")
            print(f"[OK] Available models on server: {models}")
    except Exception as e:
        print(f"[FAIL] Could not connect to {url}: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure Kaggle notebook is actively running deploy/kaggle/serve_model_only.py")
        print("2. Verify that OLLAMA_BASE_URL in your .env matches the trycloudflare.com URL")
        return False

    # 2. Test Zero-Chatter Inference
    print("\nTesting zero-chatter uncensored generation...")
    router = AIRouter()
    t1 = time.perf_counter()
    try:
        res = router.call_ollama(
            prompt="Output strictly: STATUS|ONLINE|LATENCY_TEST",
            system_prompt="You are a system probe.",
            temperature=0.0,
            format_json=False
        )
        elapsed_gen = (time.perf_counter() - t1) * 1000
        raw = res.get("raw_text", "").strip()
        print(f"[OK] Model response in {elapsed_gen:.1f}ms:")
        print(f"     \"{raw}\"")
        print("\n[SUCCESS] OpenGen on your laptop is successfully connected to the uncensored model!")
        return True
    except Exception as e:
        print(f"[FAIL] Inference probe failed: {e}")
        return False


if __name__ == "__main__":
    custom_url = sys.argv[1] if len(sys.argv) > 1 else None
    test_bridge(custom_url)
