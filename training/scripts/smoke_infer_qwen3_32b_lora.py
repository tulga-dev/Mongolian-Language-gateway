from __future__ import annotations

import argparse
import re
from pathlib import Path


FINAL_ONLY_INSTRUCTION = (
    "\u0417\u04e9\u0432\u0445\u04e9\u043d \u044d\u0446\u0441\u0438\u0439\u043d "
    "\u0445\u0430\u0440\u0438\u0443\u0433 \u041c\u043e\u043d\u0433\u043e\u043b "
    "\u0445\u044d\u043b\u044d\u044d\u0440 \u0431\u0438\u0447. \u0414\u043e\u0442\u043e\u043e\u0434 "
    "\u0431\u043e\u0434\u043e\u043b, \u0442\u0430\u0439\u043b\u0431\u0430\u0440, <think> "
    "\u0445\u044d\u0441\u044d\u0433 \u0431\u04af\u04af \u0433\u0430\u0440\u0433\u0430."
)
DEFAULT_PROMPTS = [
    "\u041c\u043e\u043d\u0433\u043e\u043b \u0445\u044d\u043b \u0434\u044d\u044d\u0440 \u0437\u044d\u044d\u043b\u0438\u0439\u043d \u0445\u04af\u0441\u044d\u043b\u0442\u0438\u0439\u043d \u0442\u043e\u0432\u0447 \u04af\u043d\u044d\u043b\u0433\u044d\u044d \u0431\u0438\u0447.",
    "\u041a\u043e\u043c\u043f\u0430\u043d\u0438\u0439\u043d \u0441\u0430\u043d\u0445\u04af\u04af\u0433\u0438\u0439\u043d \u0442\u0430\u0439\u043b\u0430\u043d\u0433\u0430\u0430\u0441 \u0437\u044d\u044d\u043b\u0434\u04af\u04af\u043b\u044d\u0433\u0447\u0438\u0434 \u0445\u044d\u0440\u044d\u0433\u0442\u044d\u0439 5 \u0433\u043e\u043b \u04af\u0437\u04af\u04af\u043b\u044d\u043b\u0442\u0438\u0439\u0433 \u0442\u0430\u0439\u043b\u0431\u0430\u0440\u043b\u0430.",
    "\u0414\u043e\u043e\u0440\u0445 \u043c\u044d\u0434\u044d\u044d\u043b\u044d\u043b \u0434\u044d\u044d\u0440 \u04af\u043d\u0434\u044d\u0441\u043b\u044d\u044d\u0434 \u0431\u043e\u0433\u0438\u043d\u043e credit memo \u0431\u0438\u0447: \u041e\u0440\u043b\u043e\u0433\u043e 120 \u0441\u0430\u044f, \u0437\u0430\u0440\u0434\u0430\u043b 80 \u0441\u0430\u044f, \u04e9\u0440 \u0442\u04e9\u043b\u0431\u04e9\u0440 60 \u0441\u0430\u044f, \u043c\u04e9\u043d\u0433\u04e9\u043d \u04af\u043b\u0434\u044d\u0433\u0434\u044d\u043b 15 \u0441\u0430\u044f.",
    "\u0417\u044d\u044d\u043b\u0434\u044d\u0433\u0447\u0438\u0439\u043d \u044d\u0440\u0441\u0434\u044d\u043b\u0438\u0439\u0433 \u041c\u043e\u043d\u0433\u043e\u043b \u0445\u044d\u043b \u0434\u044d\u044d\u0440 \u0430\u043d\u0433\u0438\u043b\u0436 \u0442\u0430\u0439\u043b\u0431\u0430\u0440\u043b\u0430.",
]
SEPARATOR = "=" * 88
THINKING_RE = re.compile(r"<think\b[^>]*>.*?</think>", re.IGNORECASE | re.DOTALL)


def str_to_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected boolean value, got {value!r}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test a trained Qwen3-32B LoRA adapter.")
    parser.add_argument("--base-model", default="Qwen/Qwen3-32B")
    parser.add_argument("--adapter", type=Path, default=Path("outputs/qwen3_32b_mn_lendex_lora"))
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--strip-thinking", nargs="?", const=True, default=True, type=str_to_bool)
    parser.add_argument("--fail-on-thinking", action="store_true")
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


def strip_thinking(text: str) -> str:
    return THINKING_RE.sub("", text).strip()


def contains_thinking(text: str) -> bool:
    lowered = text.lower()
    return "<think" in lowered or "</think>" in lowered


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
                "\u0422\u0430 Lendex \u0431\u043e\u043b\u043e\u043d Datagate-\u0434 "
                "\u0437\u043e\u0440\u0438\u0443\u043b\u0441\u0430\u043d \u043c\u043e\u043d\u0433\u043e\u043b "
                "\u0445\u044d\u043b\u043d\u0438\u0439 \u0441\u0430\u043d\u0445\u04af\u04af, "
                "\u0437\u044d\u044d\u043b\u0438\u0439\u043d \u0442\u0443\u0441\u043b\u0430\u0445. "
                "\u0422\u0430 \u044d\u0435\u043b\u0434\u044d\u0433, \u0442\u043e\u0434\u043e\u0440\u0445\u043e\u0439 "
                "\u0445\u0430\u0440\u0438\u0443\u043b\u0436, \u0437\u044d\u044d\u043b\u0438\u0439\u043d "
                "\u0437\u04e9\u0432\u0448\u04e9\u04e9\u0440\u04e9\u043b \u0430\u043c\u043b\u0430\u0445\u0433\u04af\u0439. "
                f"{FINAL_ONLY_INSTRUCTION}"
            ),
        },
        {"role": "user", "content": f"{FINAL_ONLY_INSTRUCTION}\n\n{prompt}"},
    ]


def apply_chat_template(tokenizer, messages: list[dict[str, str]]) -> str:
    kwargs = {"tokenize": False, "add_generation_prompt": True, "enable_thinking": False}
    try:
        return tokenizer.apply_chat_template(messages, **kwargs)
    except TypeError as exc:
        if "enable_thinking" not in str(exc):
            raise
        kwargs.pop("enable_thinking")
        return tokenizer.apply_chat_template(messages, **kwargs)


def generation_kwargs(tokenizer, args: argparse.Namespace) -> dict:
    eos_token_id = tokenizer.eos_token_id
    pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos_token_id
    kwargs = {
        "max_new_tokens": args.max_new_tokens,
        "do_sample": args.temperature > 0,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "eos_token_id": eos_token_id,
        "pad_token_id": pad_token_id,
        "repetition_penalty": 1.05,
    }
    return {key: value for key, value in kwargs.items() if value is not None}


def generate_answer(torch, tokenizer, model, prompt: str, args: argparse.Namespace) -> tuple[str, str, bool]:
    messages = build_messages(prompt)
    text = apply_chat_template(tokenizer, messages)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        output_ids = model.generate(**inputs, **generation_kwargs(tokenizer, args))
    generated_ids = output_ids[0][inputs["input_ids"].shape[-1] :]
    raw_answer = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    had_thinking = contains_thinking(raw_answer)
    cleaned_answer = strip_thinking(raw_answer) if args.strip_thinking else raw_answer
    return raw_answer, cleaned_answer, had_thinking


def main() -> None:
    args = parse_args()
    require_adapter(args.adapter)
    torch, tokenizer, model = load_model(args)

    print(SEPARATOR)
    print(f"Base model: {args.base_model}")
    print(f"Adapter: {args.adapter}")
    print(
        f"max_new_tokens={args.max_new_tokens} temperature={args.temperature} "
        f"top_p={args.top_p} strip_thinking={args.strip_thinking}"
    )
    print(SEPARATOR)

    thinking_seen = False
    for index, prompt in enumerate(DEFAULT_PROMPTS, start=1):
        raw_answer, answer, had_thinking = generate_answer(torch, tokenizer, model, prompt, args)
        if had_thinking:
            thinking_seen = True
            print(f"WARNING: raw output for prompt {index} contained <think> tags.")
        print(f"Prompt {index}:")
        print(prompt)
        print()
        print("Model answer:")
        print(answer or "[empty output]")
        if not args.strip_thinking and had_thinking:
            print()
            print("Raw answer included thinking tags:")
            print(raw_answer)
        print(SEPARATOR)

    if thinking_seen and args.fail_on_thinking:
        fail("Raw model output contained <think> or </think> while --fail-on-thinking was enabled.")


if __name__ == "__main__":
    main()
