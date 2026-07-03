"""embed.py — local, on-device embeddings.

One job: turn text into a 384-dim unit-normalized vector, on this machine, with
no network and no API key. Own the mind; rent only the local model.

The model is loaded **lazily** — importing this module is cheap; the ~80 MB
all-MiniLM-L6-v2 download/load happens on first real `embed()` call, then caches
locally. This keeps `cabin init` and the CLI's metadata commands fast.

Unit-normalized is load-bearing downstream: with normalized vectors, cosine
similarity == dot product, so distances are directly comparable and the
dedup/collector math (numpy) stays simple. Keep EMBED_DIM in lockstep with
db.EMBED_DIM and the vec0 FLOAT[384] companions.

THE ONE THING NOT TO DO HERE: do not let this module store anything. It computes;
it never writes to a forest table. Storage is the write door's job (forest.py),
where the laws are enforced.
"""

from __future__ import annotations

import os

import numpy as np
import sqlite_vec

# Overridable for the offline/air-gapped case (a local model path). NOTE: any
# override must also be 384-dim, or it won't match the vec0 FLOAT[384] tables.
EMBED_MODEL = os.environ.get("CABIN_EMBED_MODEL", "all-MiniLM-L6-v2")
EMBED_DIM = 384

_model = None  # lazy singleton


def _get_model():
    """Load the sentence-transformers model once, on first use.

    Local-first does not mean "never downloads" — it means no embedding API and
    no cloud storage. The model is fetched once and cached locally. If that fetch
    can't happen (offline first run), fail *humanely* and honestly, so a user
    never mistakes a missing download for a broken tool or a secret cloud call.
    """
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            try:
                # Cached path: no network, instant load.
                _model = SentenceTransformer(EMBED_MODEL, local_files_only=True)
            except Exception:
                # First run: download once, then cached forever.
                _model = SentenceTransformer(EMBED_MODEL)
        except Exception as e:
            raise RuntimeError(
                f".cabin needs a local embedding model: {EMBED_MODEL}.\n"
                "First run downloads it once (~80 MB); after that it is cached "
                "locally. No API key is used, and nothing is sent to a server.\n\n"
                f"Could not find or download the model: {e}\n\n"
                "Fix one of:\n"
                "  1. connect to the internet once and rerun, or\n"
                "  2. set CABIN_EMBED_MODEL to a local 384-dim model path."
            ) from e
    return _model


def embed(text: str) -> np.ndarray:
    """Embed one string → float32[384], unit-normalized.

    Normalization is requested from the encoder directly (normalize_embeddings),
    so the returned vector is ready for cosine-as-dot-product comparison.
    """
    vec = _get_model().encode(
        text, normalize_embeddings=True, convert_to_numpy=True
    )
    return vec.astype(np.float32)


def serialize(vec: np.ndarray) -> bytes:
    """Pack a float32 vector for a vec0 column (the sqlite-vec wire format).

    Also the byte form stored in the content table's `embedding` BLOB, so the
    two stay identical — the BLOB exists for centroid math without a vec join.
    """
    return sqlite_vec.serialize_float32(vec.astype(np.float32).tolist())


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity. For unit vectors this is just the dot product."""
    return float(np.dot(a, b))
