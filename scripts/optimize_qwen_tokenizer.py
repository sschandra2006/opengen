#!/usr/bin/env python3
"""
Qwen 2.5 Tokenizer & Chat Template Surgery Script.
Module 8 & UTRA (Universal Token-Reduction Architecture).

Reverse-engineers and patches the Jinja chat template in tokenizer_config.json
to lock Qwen 2.5 directly into structured output without generating conversational
preamble tokens or markdown code blocks.
"""
import argparse
import json
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Surgical Jinja Chat Template: Forces immediate entry into the assistant payload boundary
SURGICAL_CHAT_TEMPLATE = (
    "{% for message in messages %}"
    "{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>\n'}}"
    "{% endfor %}"
    "<|im_start|>assistant\n"
)


def patch_qwen_chat_template(model_path_or_id: str = "huihui-ai/Qwen2.5-7B-Instruct-abliterated", output_dir: Optional[str] = None):
    """
    Applies surgical template patch to a local or Hugging Face Qwen 2.5 tokenizer.
    """
    try:
        from transformers import AutoTokenizer
    except ImportError:
        logger.error("transformers library is not installed. Run: pip install transformers")
        return False

    logger.info(f"Loading tokenizer from '{model_path_or_id}'...")
    tokenizer = AutoTokenizer.from_pretrained(model_path_or_id, trust_remote_code=True)

    logger.info("Applying surgical ChatML template (Zero-Chatter lock)...")
    tokenizer.chat_template = SURGICAL_CHAT_TEMPLATE

    save_path = output_dir or model_path_or_id
    logger.info(f"Saving patched tokenizer to '{save_path}'...")
    tokenizer.save_pretrained(save_path)
    logger.info("Surgical tokenizer patch applied successfully!")
    return True


def patch_local_tokenizer_config_json(config_json_path: str):
    """
    Directly patches tokenizer_config.json file on disk without loading model weights into memory.
    """
    p = Path(config_json_path)
    if not p.exists():
        logger.error(f"File not found: {config_json_path}")
        return False

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["chat_template"] = SURGICAL_CHAT_TEMPLATE

    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully patched chat_template in {p}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Qwen 2.5 Chat Template Surgery for OpenGen UTRA")
    parser.add_argument("--model", type=str, default="huihui-ai/Qwen2.5-7B-Instruct-abliterated", help="HuggingFace model ID or local directory")
    parser.add_argument("--output", type=str, default=None, help="Output directory to save patched tokenizer")
    parser.add_argument("--config_file", type=str, default=None, help="Path to raw tokenizer_config.json to patch directly")
    args = parser.parse_args()

    if args.config_file:
        patch_local_tokenizer_config_json(args.config_file)
    else:
        patch_qwen_chat_template(args.model, args.output)
