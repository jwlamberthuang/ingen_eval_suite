"""Download only the pinned public model files required by the Week 2 run."""
import json
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    config = json.loads((ROOT/"configs/week-02.json").read_text())
    for role in ["generation", "embedding"]:
        model = config[role]
        snapshot_download(model["model_id"], revision=model["revision"],
                          allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt"], max_workers=4)
        print(f"Prepared {role}: {model['model_id']} at {model['revision']}")
