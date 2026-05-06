from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_PROMPTS = [
    "Монгол хэл дээр зээлийн хүсэлтийн товч үнэлгээ бич.",
    "Компанийн санхүүгийн тайлангаас зээлдүүлэгчид хэрэгтэй 5 гол үзүүлэлтийг тайлбарла.",
    "Доорх мэдээлэл дээр үндэслээд богино credit memo бич: Орлого 120 сая, зардал 80 сая, өр төлбөр 60 сая, мөнгөн үлдэгдэл 15 сая.",
    "Зээлдэгчийн эрсдэлийг Монгол хэл дээр ангилж тайлбарла.",
]
SEPARATOR = "=" * 88


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test a trained Qwen3-32B LoRA adapter.")
    parser.add_argument("--base-model", default="Qwen/Qwen3-32B")
    parser.add_argument("--adapter", type=Path, default=Path("outputs/qwen3_32b_mn_lendex_lora"))
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.9)
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def require_adapter(path: Path) -> None:
    if not path.exists():
        fail(f"Adapter path not found: {path}")
    if not path.is_dir():
        fail(f"Adapter path is not a directory: {path}")


def import_runtime():
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError as exc:
        fail(
            "Required inference packages are missing. Install training dependencies first: "
            "pip install -r training/requirements-train.txt. "
            f"Original import error: {exc}"
        )
    return torch, PeftModel, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def require_cuda(torch) -> None:
    if not torch.cuda.is_available():
        fail("CUDA is unavailable. This Qwen3-32B LoRA smoke test requires a GPU, such as an A100 80GB.")
    print(f"CUDA devices: {torch.cuda.device_count()}")
    print(f"Active GPU: {torch.cuda.get_device_name(0)}")


def load_model(args: argparse.Namespace):
    torch, PeftModel, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig = import_runtime()
    require_cuda(torch)

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base_model, str(args.adapter))
    model.eval()
    return torch, tokenizer, model


def build_messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Та Lendex болон Datagate-д зориулсан монгол хэлний санхүү, зээлийн туслах. "
                "Та эелдэг, тодорхой хариулж, зээлийн зөвшөөрөл амлахгүй."
            ),
        },
        {"role": "user", "content": prompt},
    ]


def generate_answer(torch, tokenizer, model, prompt: str, args: argparse.Namespace) -> str:
    messages = build_messages(prompt)
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            do_sample=args.temperature > 0,
            temperature=args.temperature,
            top_p=args.top_p,
            repetition_penalty=1.05,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated_ids = output_ids[0][inputs["input_ids"].shape[-1] :]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def main() -> None:
    args = parse_args()
    require_adapter(args.adapter)
    torch, tokenizer, model = load_model(args)

    print(SEPARATOR)
    print(f"Base model: {args.base_model}")
    print(f"Adapter: {args.adapter}")
    print(f"max_new_tokens={args.max_new_tokens} temperature={args.temperature} top_p={args.top_p}")
    print(SEPARATOR)

    for index, prompt in enumerate(DEFAULT_PROMPTS, start=1):
        answer = generate_answer(torch, tokenizer, model, prompt, args)
        print(f"Prompt {index}:")
        print(prompt)
        print()
        print("Model answer:")
        print(answer or "[empty output]")
        print(SEPARATOR)


if __name__ == "__main__":
    main()
