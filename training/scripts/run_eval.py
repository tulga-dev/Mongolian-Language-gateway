from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.evals.metrics import average_score
from training.evals.scoring import heuristic_score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/eval_results.json"))
    args = parser.parse_args()
    scores = []
    with args.benchmark.open("r", encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            scores.append({"id": item["id"], "score": heuristic_score(item.get("expected", "")), "notes": "Heuristic placeholder; replace with Qwen teacher judge."})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = {"benchmark": str(args.benchmark), "average_score": average_score(scores), "scores": scores}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
