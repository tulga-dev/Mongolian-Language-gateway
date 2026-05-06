from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def require_cuda() -> None:
    import torch

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for real Qwen3-32B QLoRA training.")
    print(f"CUDA devices: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.get_device_name(0)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Qwen3-32B Mongolian Lendex QLoRA adapter.")
    parser.add_argument("--config", type=Path, default=Path("training/configs/qwen3_32b_mn_sft.yaml"))
    parser.add_argument("--dry-run", action="store_true", help="Validate config/import path without loading model weights.")
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    output_dir = config["training"]["output_dir"]

    if args.dry_run:
        print(f"Config OK: base_model={config['model']['base_model']} output_dir={output_dir}")
        return

    require_cuda()

    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    quant_config = config["quantization"]
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=quant_config["load_in_4bit"],
        bnb_4bit_quant_type=quant_config["bnb_4bit_quant_type"],
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=quant_config["bnb_4bit_use_double_quant"],
    )

    tokenizer = AutoTokenizer.from_pretrained(
        config["model"]["base_model"],
        trust_remote_code=config["model"].get("trust_remote_code", True),
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        config["model"]["base_model"],
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=config["model"].get("trust_remote_code", True),
        attn_implementation=config["model"].get("attn_implementation"),
    )
    model.config.use_cache = False

    lora_config = config["lora"]
    peft_config = LoraConfig(
        r=lora_config["r"],
        lora_alpha=lora_config["alpha"],
        lora_dropout=lora_config["dropout"],
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=lora_config["target_modules"],
    )

    train_dataset = load_dataset("json", data_files=config["data"]["train_file"], split="train")
    eval_dataset = load_dataset("json", data_files=config["data"]["validation_file"], split="train")

    training_config = config["training"]
    training_args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=training_config["num_train_epochs"],
        per_device_train_batch_size=training_config["per_device_train_batch_size"],
        per_device_eval_batch_size=training_config["per_device_eval_batch_size"],
        gradient_accumulation_steps=training_config["gradient_accumulation_steps"],
        learning_rate=training_config["learning_rate"],
        lr_scheduler_type=training_config["lr_scheduler_type"],
        warmup_ratio=training_config["warmup_ratio"],
        logging_steps=training_config["logging_steps"],
        save_steps=training_config["save_steps"],
        eval_steps=training_config["eval_steps"],
        eval_strategy=training_config["evaluation_strategy"],
        save_total_limit=training_config["save_total_limit"],
        bf16=training_config["bf16"],
        fp16=training_config["fp16"],
        gradient_checkpointing=training_config["gradient_checkpointing"],
        optim=training_config["optim"],
        max_grad_norm=training_config["max_grad_norm"],
        report_to=training_config["report_to"],
        max_length=config["data"]["max_seq_length"],
        dataset_kwargs={"skip_prepare_dataset": True},
    )

    def formatting_func(example: dict) -> str:
        return tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False)

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        peft_config=peft_config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        formatting_func=formatting_func,
    )
    trainer.train()
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Saved adapter to {output_dir}")


if __name__ == "__main__":
    main()
