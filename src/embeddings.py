"""Pinned multilingual E5 inference and portable, download-free embedding replay."""

import json
from pathlib import Path
import numpy as np


class SentenceEncoder:
    """Cache full prefixed inputs; reject over-limit inputs instead of truncating."""

    def __init__(self, model_id="intfloat/multilingual-e5-base", revision=None,
                 device="cpu", batch_size=16, max_tokens=512, model=None):
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_id, revision=revision, device=device,
                                        trust_remote_code=False)
        self.model, self.model_id, self.revision = model, model_id, revision
        self.batch_size, self.max_tokens = batch_size, max_tokens
        self.cache = {}

    def encode(self, texts, prefix="query: "):
        """Return normalized vectors for exact inputs with declared E5 prefixes."""
        if prefix not in {"query: ", "passage: "}:
            raise ValueError("Unrecognized E5 prefix")
        keys = [prefix+t for t in texts]
        missing = list(dict.fromkeys(k for k in keys if k not in self.cache))
        for text in missing:
            if len(self.model.tokenizer.encode(text, add_special_tokens=True)) > self.max_tokens:
                raise ValueError("Embedding input exceeds the declared token limit")
        if missing:
            values = self.model.encode(missing, batch_size=self.batch_size,
                                       normalize_embeddings=True, convert_to_numpy=True,
                                       show_progress_bar=False)
            self.cache.update(zip(missing, values))
        return [self.cache[key] for key in keys]

    def save(self, directory):
        """Save only input text and vectors, never model weights or machine paths."""
        directory = Path(directory)
        keys = sorted(self.cache)
        np.savez_compressed(directory/"embeddings.npz", vectors=np.asarray([self.cache[k] for k in keys]))
        metadata = {"model_id": self.model_id, "revision": self.revision,
                    "max_tokens": self.max_tokens, "inputs": keys,
                    "pooling": "attention_mask_mean", "normalization": "L2"}
        (directory/"embeddings.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')


class ReplayEncoder:
    """Recompute scores from saved vectors without downloading a language model."""

    def __init__(self, directory):
        directory = Path(directory)
        metadata = json.loads((directory/"embeddings.json").read_text())
        with np.load(directory/"embeddings.npz", allow_pickle=False) as stored:
            self.cache = dict(zip(metadata["inputs"], stored["vectors"]))
        self.model_id, self.revision = metadata["model_id"], metadata["revision"]

    def encode(self, texts, prefix="query: "):
        """Look up exact prefixed inputs; missing vectors are explicit errors."""
        return [self.cache[prefix+text] for text in texts]
