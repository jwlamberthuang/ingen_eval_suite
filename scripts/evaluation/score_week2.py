"""Calibrate, score, or replay the frozen Week 2 experiment."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.experiment import calibrate_run, score_run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["calibrate", "score", "replay"])
    parser.add_argument("--config", type=Path, default=ROOT/"configs/week-02.json")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.stage == "calibrate":
        calibrate_run(ROOT, config)
    else:
        score_run(ROOT, config, replay=args.stage == "replay")
