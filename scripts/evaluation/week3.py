"""Preflight, freeze, generate, inspect claims, score, and replay Week 3 runs."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.datasets.v2.manage_dataset import loads
from src.week3_experiment import (preflight, freeze_run, calibrate_stage,
                                  generate_stage, review_template, score_stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("preflight", "freeze", "calibrate", "generate", "extract", "review-template", "score", "replay"))
    parser.add_argument("--config", type=Path, default=ROOT / "configs/week-03.json")
    args = parser.parse_args()
    config = loads(args.config.read_text())
    stages = {"preflight": lambda: preflight(ROOT, config),
              "freeze": lambda: {"status": freeze_run(ROOT, config)["status"]},
              "calibrate": lambda: calibrate_stage(ROOT, config),
              "generate": lambda: generate_stage(ROOT, config),
              "extract": lambda: generate_stage(ROOT, config, "claims"),
              "review-template": lambda: review_template(ROOT, config),
              "score": lambda: score_stage(ROOT, config),
              "replay": lambda: score_stage(ROOT, config, replay=True)}
    try:
        result = stages[args.stage]()
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        # Exception text can contain machine paths; show a portable category.
        reason = (str(exc) if isinstance(exc, ValueError) and str(ROOT) not in str(exc)
                  else "Required artifact is unavailable or the output already exists")
        print(json.dumps({"stage": args.stage, "status": "blocked", "error_type": type(exc).__name__, "reason": reason}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
