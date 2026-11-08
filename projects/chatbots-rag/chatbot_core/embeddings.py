"""Embeddings and semantic similarity.

Two implementations ship with the course:

``HashingEmbedder``
    Deterministic, dependency-free, and offline. It hashes word and character
    n-grams into a fixed-width vector and L2-normalizes the result. It is *not*
    a trained semantic model: it captures surface overlap and morphology, which
    is enough to teach cosine similarity and to test a retrieval pipeline without
    a download. Do not describe its output as "meaning".

``SentenceTransformerEmbedder``
    Optional. Wraps a real sentence-transformer when the package and a local
    model are available. Nothing in the offline path imports it at module load.

Both expose ``dim`` and ``embed(texts) -> numpy.ndarray`` so the rest of the
pipeline is unaware of which one it received.
"""

from __future__ import annotations

import hashlib
import re
from typing import Protocol, Sequence

import numpy as np

WORD = re.compile(r"[a-z0-9']+")


class Embedder(Protocol):
    """Minimal interface the retrieval layer depends on."""

    dim: int

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        ...


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class HashingEmbedder:
    """N-gram hashing embedder: deterministic, offline, and honest about it."""

    def __init__(self, dim: int = 512, include_char_ngrams: bool = True) -> None:
        if dim < 32:
            raise ValueError("dim must be at least 32")
        self.dim = dim
        self.include_char_ngrams = include_char_ngrams

    def _features(self, text: str) -> list[str]:
        words = WORD.findall(text.lower())
        features = list(words)
        features.extend(f"{a}_{b}" for a, b in zip(words, words[1:]))
        if self.include_char_ngrams:
            for word in words:
                padded = f"#{word}#"
                features.extend(padded[i : i + 3] for i in range(max(len(padded) - 2, 1)))
        return features

    def _bucket(self, feature: str) -> int:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % self.dim

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for feature in self._features(text):
                matrix[row, self._bucket(feature)] += 1.0
        return _normalize(matrix)

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]


class SentenceTransformerEmbedder:
    """Optional wrapper around ``sentence-transformers``.

    Raises ``RuntimeError`` with an actionable message when the package or model
    is unavailable, so the caller can fall back to ``HashingEmbedder`` instead of
    crashing the lab.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "sentence-transformers is not installed. Install requirements/llm.txt, "
                "or use HashingEmbedder for the offline path."
            ) from exc
        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed(self, texts: Sequence[str]) -> np.ndarray:  # pragma: no cover - optional
        return _normalize(np.asarray(self._model.encode(list(texts)), dtype=np.float32))


def cosine_similarity(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    """Cosine similarity for already-normalized rows."""
    if matrix.size == 0:
        return np.zeros(0, dtype=np.float32)
    return matrix @ vector


def default_embedder(prefer_semantic: bool = False) -> Embedder:
    """Return the best available embedder, defaulting to the offline one."""
    if prefer_semantic:
        try:
            return SentenceTransformerEmbedder()
        except RuntimeError:
            pass
    return HashingEmbedder()
