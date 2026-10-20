"""Generate the pinned local baseline; all outputs remain keyed by case ID."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.generation import generate_run
from src.experiment import dataset_records

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT/"configs/week-02.json")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    dataset_records(ROOT, config)
    generate_run(ROOT, config)
