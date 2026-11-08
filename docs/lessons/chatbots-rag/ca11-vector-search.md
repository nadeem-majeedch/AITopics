# CA11 - Vector search and retrieval {#ca11}

**Section path:** [Overview](index.md) · **Module 11** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | CA09, CA10 |
| **You will produce** | A retrieval comparison table: lexical, dense, and hybrid, on the same questions |

## Why this module exists

Retrieval is where most RAG failures originate, and it is the part students measure
least. This module gives you three retrievers, one question set, and the discipline to
compare them instead of assuming the newest one wins.

## Three retrievers, one interface

Every retriever returns `RetrievalResult` objects carrying the chunk, the score, and the
rank, so downstream code and evaluation never care which one produced them.

```python
@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float
    rank: int
    retriever: str = "vector"
```

### Dense: exact flat search

```python
scores = cosine_similarity(self.matrix, self.embedder.embed_one(query))
order = np.argsort(-scores)[:k]
```

A **flat** index compares the query against every chunk. With 41 chunks that is
microseconds; with 5 million it is hopeless. Flat is the right default because it is
exact and simple, and because approximate indexes introduce a recall loss you would then
have to measure separately.

### Sparse: BM25

Okapi BM25 scores a document by term frequency, inverse document frequency, and length
normalisation:

```python
score += self._idf(term) * (tf * (self.k1 + 1)) / (
    tf + self.k1 * (1 - self.b + self.b * length / self.avg_len)
)
```

It has no notion of meaning, and it is startlingly strong on documentation. In this
section's corpus, BM25 finds the refund passage for "refund window for a paid workshop"
at rank 1. That is the baseline any embedding model must beat, and it is cheap.

### Hybrid: normalised score fusion

```python
fused[chunk_id] = (
    self.vector_weight * dense_norm.get(chunk_id, 0.0)
    + (1 - self.vector_weight) * sparse_norm.get(chunk_id, 0.0)
)
```

Min-max normalisation per query, then a weighted sum. It is crude and explainable: a
student can recompute any fused score by hand. `vector_weight=0.0` is BM25-only,
`1.0` is dense-only, and `0.6` is the default.

## Measured comparison

The harness in `project_g_evaluation.py` scores four configurations on the same
questions. On the synthetic corpus with the offline embedder and the extractive client:

| System | Answer accuracy | Answerable accuracy | hit@k | Mean latency |
| --- | --- | --- | --- | --- |
| prompt-only (no retrieval) | 0.000 | 0.000 | 0.000 | ~0.01 ms |
| BM25 | 0.667 | 0.667 | 1.000 | ~0.84 ms |
| dense (hashing) | 0.500 | 0.500 | 1.000 | ~0.77 ms |
| hybrid | 0.667 | 0.667 | 1.000 | ~0.76 ms |

Read these numbers carefully, because each one teaches something:

- **`hit@k` is 1.0 everywhere.** Retrieval found a gold document in the top 4 for every
  answerable question. The remaining errors are *generation* errors, not retrieval ones.
  Without this column you would tune the wrong component.
- **Dense alone is worse than BM25 here.** The hashing embedder captures character
  overlap, not meaning; BM25's term weighting is simply better at this task. This is why
  the section does not present embeddings as an automatic upgrade.
- **Hybrid ties BM25.** Fusion helps when the two retrievers fail on *different*
  questions. Here they fail on the same ones, so fusion cannot add anything. That is a
  finding, and reporting it is better than hiding it.

## Choosing k

| `k` | Effect |
| --- | --- |
| 1 | Fast, brittle; one ranking mistake is fatal |
| 4 (default) | Fits a small context; enough to recover from one bad rank |
| 10+ | Better recall, more noise, more tokens, higher chance of a conflicting passage |

`k` is a context-budget decision as much as a quality one. Module 4's arithmetic
applies: retrieve more and you have less room for history.

## Approximate search, when it matters

| Index | Idea | Trade-off |
| --- | --- | --- |
| Flat | Compare everything | Exact, linear cost |
| IVF | Cluster, search nearby cells | Fast, misses some neighbours |
| HNSW | Graph navigation | Very fast, memory-heavy, approximate |

You do not need any of these at course scale. You do need to know that switching to one
changes `hit@k`, so it becomes part of your evaluation rather than an invisible setting.

## Metadata filters

An index should not only rank; it must respect permission. If a chunk belongs to a
document the user cannot open, it must be excluded *before* scoring:

```python
allowed = [chunk for chunk in chunks if chunk.doc_id in permitted_doc_ids]
```

Module 16 treats this as an access-control requirement. Retrieving a forbidden passage
and then refusing to quote it still leaks that it exists, and often leaks its content
through the model's answer.

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Gold passage never retrieved | Chunk missing, or heading excluded from index | Search for a distinctive phrase from the passage |
| Scores are all similar | Weak embedder, or normalisation missing | Compare with BM25 on the same query |
| Hybrid worse than its parts | Weights or normalisation wrong | Print dense and sparse scores before fusion |
| Retrieval improves but answers do not | Generation is the bottleneck | Compare `hit@k` with `answer_accuracy` |
| Results vary between runs | Non-deterministic embedder or index rebuild | Pin the model and re-index |
| Duplicate results fill the top k | Overlapping chunks | Deduplicate before indexing |

## Checkpoint

- [ ] You can describe BM25's three components in one sentence each.
- [ ] You can explain why hybrid fusion can fail to beat its best component.
- [ ] You can state what `hit@k` measures and what it does not.
- [ ] You can name one access-control consequence of retrieval.

## Next step

Read [CA12 - Retrieval-augmented generation](ca12-rag.md), where retrieval and the model
are joined under a policy.
