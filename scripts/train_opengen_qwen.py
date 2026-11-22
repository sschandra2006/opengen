#!/usr/bin/env python3
"""
OpenGen Qwen 2.5 7B QLoRA Fine-Tuning Script using Unsloth.
Target Runtime: Kaggle Free Tier Tesla T4 GPU (16GB VRAM, 30GB RAM).
Execution Specs:
- VRAM Usage: < 6GB
- Precision: 4-bit NF4 Quantization
- Training Duration: ~12-18 minutes for 100-200 steps
- Output: ~25MB LoRA adapter (safe for Git) + GGUF (q4_k_m) for local Ollama serving.
"""
import os
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Sample OpenGen Dense IR Training Examples
DEFAULT_TRAINING_EXAMPLES = [
    {
        "prompt": "<|im_start|>system\nYou are the OpenGen Semantic Extractor. Output strictly: SKU|NAME|CAT|MRP|PRICE<|im_end|>\n<|im_start|>user\nExtract: Mani Traders Full Cream Milk 1L MRP 66 sale 62, Curd 400g MRP 40 sale 38<|im_end|>\n<|im_start|>assistant\n",
        "completion": "MM-01|Full Cream Milk 1L|Dairy|66.0|62.0\nMM-02|Curd 400g|Dairy|40.0|38.0<|im_end|>"
    },
    {
        "prompt": "<|im_start|>system\nYou are the OpenGen Semantic Extractor. Output strictly: SKU|NAME|CAT|MRP|PRICE<|im_end|>\n<|im_start|>user\nExtract: Pure Cow Ghee 500ml ₹380 discounted to ₹365, Buffalo Paneer 200g ₹95 sale ₹90<|im_end|>\n<|im_start|>assistant\n",
        "completion": "MM-03|Pure Cow Ghee 500ml|Dairy|380.0|365.0\nMM-04|Buffalo Paneer 200g|Dairy|95.0|90.0<|im_end|>"
    },
    {
        "prompt": "<|im_start|>system\nYou are the OpenGen Semantic Extractor. Output strictly: SKU|NAME|CAT|MRP|PRICE<|im_end|>\n<|im_start|>user\nExtract: Gulab Jamun 1kg ₹320 offer ₹299, Fresh Bread 400g ₹45 offer ₹42<|im_end|>\n<|im_start|>assistant\n",
        "completion": "MM-05|Gulab Jamun 1kg|Sweets|320.0|299.0\nMM-06|Fresh Bread 400g|Bakery|45.0|42.0<|im_end|>"
    }
]


def train(
    model_name: str = "huihui-ai/Qwen2.5-7B-Instruct-abliterated",
    output_adapter_dir: str = "models/adapters/opengen_qwen_lora",
    export_gguf: bool = False,
    gguf_dir: str = "opengen_qwen_q4",
    max_steps: int = 50,
    learning_rate: float = 2e-4
):
    try:
        from unsloth import FastLanguageModel
        import torch
        from datasets import Dataset
        from trl import SFTTrainer
        from transformers import TrainingArguments
    except ImportError as e:
        logger.error(f"Required training packages missing ({e}). Run in Kaggle or install: pip install unsloth trl datasets")
        return

    logger.info(f"Loading 4-bit Quantized Base Model '{model_name}'...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )

    logger.info("Injecting LoRA adapters targeting all linear projection layers...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth"
    )

    dataset = Dataset.from_list([
        {"text": ex["prompt"] + ex["completion"]} for ex in DEFAULT_TRAINING_EXAMPLES
    ])

    logger.info("Initializing SFTTrainer...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            max_steps=max_steps,
            learning_rate=learning_rate,
            fp16=not torch.cuda.is_bf16_supported(),
            logging_steps=5,
            optim="adamw_8bit",
            output_dir="qwen_opengen_output"
        ),
    )

    logger.info(f"Beginning training for {max_steps} steps...")
    trainer.train()

    # Save lightweight LoRA adapter (~25MB)
    out_p = Path(output_adapter_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving ~25MB LoRA adapter to '{out_p}'...")
    model.save_pretrained(str(out_p))
    tokenizer.save_pretrained(str(out_p))

    # Export to GGUF if requested
    if export_gguf:
        logger.info(f"Exporting GGUF (q4_k_m) to '{gguf_dir}'...")
        model.save_pretrained_gguf(gguf_dir, tokenizer, quantization_method="q4_k_m")
        logger.info("GGUF export completed.")

    logger.info("Fine-tuning pipeline completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenGen Qwen 2.5 7B QLoRA Fine-Tuning")
    parser.add_argument("--model", type=str, default="huihui-ai/Qwen2.5-7B-Instruct-abliterated", help="Base model name or Kaggle input path")
    parser.add_argument("--output_adapter", type=str, default="models/adapters/opengen_qwen_lora", help="Adapter destination")
    parser.add_argument("--export_gguf", action="store_true", help="Whether to export GGUF for Ollama")
    parser.add_argument("--gguf_dir", type=str, default="opengen_qwen_q4", help="GGUF export directory")
    parser.add_argument("--max_steps", type=int, default=50, help="Max training steps")
    args = parser.parse_args()

    train(
        model_name=args.model,
        output_adapter_dir=args.output_adapter,
        export_gguf=args.export_gguf,
        gguf_dir=args.gguf_dir,
        max_steps=args.max_steps
    )
