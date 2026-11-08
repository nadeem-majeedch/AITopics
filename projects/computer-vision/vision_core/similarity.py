"""Image embeddings and similarity search.

Two embedders, for two lessons:

* :func:`histogram_embedding` - colour and coarse structure, no training. Shows
  that "similar" is defined by the embedding, not by the picture: two photos of
  the same object under different light land far apart.
* :func:`~vision_core.transfer.extract_features` - a trained CNN's pooled
  features. Same index, better neighbours, and the comparison is the measurement.

The index is brute-force cosine search. At this scale that is faster than any
approximate structure, and it makes the recall arithmetic obvious.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from .datasets import ImageRecord
from .imaging import resize, to_float


def histogram_embedding(image: np.ndarray, bins: int = 4, thumb: int = 8) -> np.ndarray:
    """A 128-dim vector: 4x4x4 colour histogram plus an 8x8 luminance thumbnail.

    Colour tells you "same palette", the thumbnail tells you "same layout". Both
    are appearance, not semantics - a red circle and a red square are closer than
    a red circle and a blue circle, which is worth knowing before trusting a
    similarity demo.
    """
    arr = to_float(image)
    # Quantize each channel into `bins` levels and count the 3-D joint histogram.
    quantized = np.clip((arr * bins).astype(np.int16), 0, bins - 1)
    flat = quantized[..., 0] * bins * bins + quantized[..., 1] * bins + quantized[..., 2]
    hist = np.bincount(flat.reshape(-1), minlength=bins**3).astype(np.float32)
    hist /= max(1.0, hist.sum())

    small = resize((to_float(image) * 255).astype(np.uint8), (thumb, thumb), resample="bilinear")
    gray = small.mean(axis=2).astype(np.float32) / 255.0

    vector = np.concatenate([hist, gray.reshape(-1)])
    return vector / max(1e-6, float(np.linalg.norm(vector)))


@dataclass
class SearchHit:
    index: int
    score: float
    label: int
    source_id: str

    def as_dict(self) -> dict:
        return {"index": self.index, "score": round(self.score, 4), "label": self.label, "source_id": self.source_id}


@dataclass
class EmbeddingIndex:
    """Brute-force cosine index over embeddings."""

    embeddings: np.ndarray = field(default_factory=lambda: np.zeros((0, 0), dtype=np.float32))
    labels: list[int] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_records(cls, records: Sequence[ImageRecord], embedder=histogram_embedding) -> "EmbeddingIndex":
        vectors = np.stack([embedder(r.image) for r in records]) if records else np.zeros((0, 128), dtype=np.float32)
        return cls(embeddings=vectors.astype(np.float32), labels=[r.label for r in records], source_ids=[r.source_id for r in records])

    @classmethod
    def from_vectors(cls, vectors: np.ndarray, labels: Sequence[int], source_ids: Sequence[str] | None = None) -> "EmbeddingIndex":
        vectors = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return cls(embeddings=vectors / np.maximum(norms, 1e-12), labels=list(labels), source_ids=list(source_ids or []))

    def __len__(self) -> int:
        return len(self.labels)

    def search(self, vector: np.ndarray, k: int = 5) -> list[SearchHit]:
        """Top-k cosine neighbours, normalizing the query the same way as the gallery."""
        if len(self) == 0:
            return []
        q = np.asarray(vector, dtype=np.float32).reshape(-1)
        q = q / max(1e-12, float(np.linalg.norm(q)))
        scores = self.embeddings @ q
        order = np.argsort(-scores)[: max(1, min(k, len(self)))]
        return [SearchHit(int(i), float(scores[i]), self.labels[int(i)], self.source_ids[int(i)]) for i in order]

    def precision_at_k(self, queries: Sequence[ImageRecord], k: int = 5, embedder=histogram_embedding, exclude_self: bool = True) -> dict:
        """Fraction of returned neighbours sharing the query's label.

        ``exclude_self`` matters: leaving the query in the gallery gives every
        query a perfect top-1 hit and makes the metric meaningless. The lab asks
        students to run it both ways and explain the difference.
        """
        hits, correct = 0, 0
        per_query = []
        for query in queries:
            results = self.search(embedder(query.image), k=k + (1 if exclude_self else 0))
            if exclude_self:
                results = [r for r in results if r.source_id != query.source_id][:k]
            else:
                results = results[:k]
            if not results:
                continue
            good = sum(1 for r in results if r.label == query.label)
            hits += len(results)
            correct += good
            per_query.append(good / len(results))
        return {
            "precision_at_k": correct / max(1, hits),
            "k": k,
            "n_queries": len(per_query),
            "mean_per_query": float(np.mean(per_query)) if per_query else 0.0,
            "exclude_self": exclude_self,
        }


def nearest_neighbour_accuracy(index: EmbeddingIndex, queries: Sequence[ImageRecord], embedder=histogram_embedding) -> float:
    """1-NN label accuracy, excluding hits from the query's own source."""
    correct = 0
    counted = 0
    for query in queries:
        for hit in index.search(embedder(query.image), k=5):
            if hit.source_id == query.source_id:
                continue
            correct += int(hit.label == query.label)
            counted += 1
            break
    return correct / max(1, counted)


def format_hits(hits: Sequence[SearchHit], class_names: Sequence[str]) -> str:
    lines = [f"{'rank':>4} {'score':>7} {'label':>12} {'source':>16}"]
    for rank, hit in enumerate(hits, start=1):
        label = class_names[hit.label] if 0 <= hit.label < len(class_names) else str(hit.label)
        lines.append(f"{rank:>4} {hit.score:>7.4f} {label:>12} {hit.source_id:>16}")
    return "\n".join(lines)
