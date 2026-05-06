from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_OUTPUT = Path("outputs/eval_report.json")


def mock_report() -> dict:
    return {
        "mode": "mock",
        "adapter": "outputs/qwen3_32b_mn_lendex_lora",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmarks": [
            {"name": "GeneralMongolianBench-v1", "score": 0.8, "notes": "Mock score; run real evaluator after training."},
            {"name": "MongolianBankBench-v1", "score": 0.8, "notes": "Mock score; compliance judge not invoked."},
        ],
        "teacher_evaluator": "Qwen3-235B-A22B-Instruct-2507",
        "requires_real_eval": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a Qwen adapter; mock mode is safe for setup.")
    parser.add_argument("--adapter", type=Path, default=Path("outputs/qwen3_32b_mn_lendex_lora"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    if not args.mock:
        raise SystemExit("Real adapter evaluation is not wired here yet. Use --mock for setup validation.")

    report = mock_report()
    report["adapter"] = str(args.adapter)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
