"""Vector search, a keyword baseline, and hybrid retrieval.

Three retrievers are provided so that Module 11 and Project E can compare them:

``VectorIndex``  dense cosine similarity over embedded chunks (flat index)
``BM25``         sparse keyword scoring, a fair lexical baseline
``HybridRetriever``  normalized score fusion of the two

Every retriever returns ``RetrievalResult`` objects, which carry the score, the
rank, and the chunk, so citations and evaluation can work from the same object.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .documents import Chunk, tokenize
from .embeddings import Embedder, cosine_similarity


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float
    rank: int
    retriever: str = "vector"

    def as_dict(self) -> dict:
        payload = self.chunk.as_dict()
        payload.update({"score": round(self.score, 6), "rank": self.rank, "retriever": self.retriever})
        return payload


class VectorIndex:
    """A flat exact-search index, appropriate for hundreds to low thousands of chunks."""

    def __init__(self, chunks: Sequence[Chunk], embedder: Embedder) -> None:
        if not chunks:
            raise ValueError("VectorIndex needs at least one chunk")
        self.chunks = list(chunks)
        self.embedder = embedder
        self.matrix = embedder.embed([chunk.retrieval_text for chunk in self.chunks])

    def search(self, query: str, k: int = 4) -> list[RetrievalResult]:
        if k <= 0:
            raise ValueError("k must be positive")
        scores = cosine_similarity(self.matrix, self.embedder.embed_one(query))
        order = np.argsort(-scores)[:k]
        return [
            RetrievalResult(chunk=self.chunks[i], score=float(scores[i]), rank=rank, retriever="vector")
            for rank, i in enumerate(order, start=1)
        ]

    def __len__(self) -> int:
        return len(self.chunks)


class BM25:
    """Okapi BM25 over the same chunk set; the lexical baseline for comparisons."""

    def __init__(self, chunks: Sequence[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        if not chunks:
            raise ValueError("BM25 needs at least one chunk")
        self.chunks = list(chunks)
        self.k1 = k1
        self.b = b
        self.tokens = [tokenize(chunk.retrieval_text) for chunk in self.chunks]
        self.doc_freq = Counter()
        for tokens in self.tokens:
            self.doc_freq.update(set(tokens))
        self.avg_len = sum(len(t) for t in self.tokens) / len(self.tokens) or 1.0

    def _idf(self, term: str) -> float:
        n = len(self.chunks)
        df = self.doc_freq.get(term, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def search(self, query: str, k: int = 4) -> list[RetrievalResult]:
        query_terms = tokenize(query)
        scored: list[tuple[float, int]] = []
        for index, tokens in enumerate(self.tokens):
            counts = Counter(tokens)
            length = len(tokens) or 1
            score = 0.0
            for term in query_terms:
                if term not in counts:
                    continue
                tf = counts[term]
                score += self._idf(term) * (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * length / self.avg_len)
                )
            if score > 0:
                scored.append((score, index))
        scored.sort(key=lambda item: -item[0])
        return [
            RetrievalResult(chunk=self.chunks[i], score=score, rank=rank, retriever="bm25")
            for rank, (score, i) in enumerate(scored[:k], start=1)
        ]


class HybridRetriever:
    """Score-fusion retriever: dense plus lexical, normalized per query.

    Fusion is a weighted sum of each retriever's min-max normalized scores. It is
    simple on purpose: a student can compute it by hand and explain any result.
    """

    def __init__(
        self,
        chunks: Sequence[Chunk],
        embedder: Embedder,
        vector_weight: float = 0.6,
    ) -> None:
        if not 0.0 <= vector_weight <= 1.0:
            raise ValueError("vector_weight must be in [0, 1]")
        self.vector = VectorIndex(chunks, embedder)
        self.bm25 = BM25(chunks)
        self.vector_weight = vector_weight

    @staticmethod
    def _normalize(results: Sequence[RetrievalResult]) -> dict[str, float]:
        if not results:
            return {}
        top = max(r.score for r in results)
        if top <= 0:
            return {r.chunk.chunk_id: 0.0 for r in results}
        return {r.chunk.chunk_id: r.score / top for r in results}

    def search(self, query: str, k: int = 4, pool: int = 20) -> list[RetrievalResult]:
        dense = self.vector.search(query, k=pool)
        sparse = self.bm25.search(query, k=pool)
        dense_norm = self._normalize(dense)
        sparse_norm = self._normalize(sparse)

        by_id: dict[str, Chunk] = {r.chunk.chunk_id: r.chunk for r in dense}
        by_id.update({r.chunk.chunk_id: r.chunk for r in sparse})

        fused = {
            chunk_id: self.vector_weight * dense_norm.get(chunk_id, 0.0)
            + (1 - self.vector_weight) * sparse_norm.get(chunk_id, 0.0)
            for chunk_id in by_id
        }
        ranked = sorted(fused.items(), key=lambda item: -item[1])[:k]
        return [
            RetrievalResult(chunk=by_id[chunk_id], score=score, rank=rank, retriever="hybrid")
            for rank, (chunk_id, score) in enumerate(ranked, start=1)
        ]
