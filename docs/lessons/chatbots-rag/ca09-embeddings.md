# CA09 - Embeddings and semantic similarity {#ca09}

**Section path:** [Overview](index.md) · **Module 9** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | CA02, F03 (NumPy) |
| **You will produce** | A similarity table for a small set of sentences, and a written account of what it does not capture |

## Why this module exists

Retrieval is a search problem, and search needs a notion of "close". Embeddings turn
text into vectors so that distance means something. The danger is that students assume
distance *means meaning*, and then trust a number they have not inspected.

This module builds a working embedder from scratch, measures its limits, and then
introduces the trained alternative it stands in for.

## What an embedding is

An **embedding** is a fixed-length vector of numbers representing a piece of text. A
**similarity function** compares two vectors. The standard choice is cosine similarity:
the cosine of the angle between them, which ignores magnitude and ranges from -1 to 1.

```python
scores = cosine_similarity(matrix, query_vector)   # rows already L2-normalised
```

Because the rows are normalised, the dot product *is* the cosine. That is why
`embeddings.py` normalises once at embed time instead of normalising on every query.

## The offline embedder, and its honesty

```python
class HashingEmbedder:
    def __init__(self, dim: int = 512, include_char_ngrams: bool = True) -> None:
        self.dim = dim
        self.include_char_ngrams = include_char_ngrams
```

It builds features from words, word pairs, and character trigrams, hashes each feature
into one of `dim` buckets, counts collisions, and normalises.

What that buys: deterministic, dependency-free, offline, fast.

What it does **not** buy: meaning. "Refund" and "reimbursement" are unrelated to this
embedder; "refund" and "refunding" are close because they share character trigrams.

Measured consequence, from this section's own runs: the question *"What is the capital
of Mongolia?"* scores **0.894** cosine against a chunk about context windows. A high
similarity score is not evidence. That number is why the pipeline has a lexical-support
gate (Module 12) rather than a similarity threshold alone.

!!! warning "Read the score as overlap, not understanding"
    If you describe `HashingEmbedder` output as "semantic similarity" in a report, you
    are making a claim the module cannot support. The trained model in the next section
    is the one that earns that phrase.

## The trained alternative

```python
class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        ...
        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())
```

Imported lazily, behind `requirements/llm.txt`. Roughly 90 MB for the small model, and
it runs on CPU in milliseconds for short passages.

| | Hashing | Trained sentence-transformer |
| --- | --- | --- |
| Download | none | ~90 MB |
| Captures paraphrase | No | Yes |
| Deterministic across machines | Yes | Yes, if the weights are pinned |
| Cost per chunk | Microseconds | Milliseconds |
| Honest label | Lexical overlap | Semantic similarity |

`default_embedder()` returns the hashing embedder unless you ask for the other, and
falls back silently-but-visibly if the package is missing. Silent fallback in a report
is a correctness bug; silent fallback in a laboratory default is a usability choice.
Know which one you are writing.

## The dimension trade-off

| `dim` | Effect |
| --- | --- |
| 64 | Fast, heavy collisions, poor discrimination |
| 512 (default) | Good balance for a few hundred chunks |
| 4096 | Fewer collisions, more memory, slower search |

Dimension is a memory-versus-resolution choice. With 41 chunks, 512 is generous; with
500,000 chunks you would move to an approximate index (Module 11) rather than a bigger
vector.

## Measuring similarity honestly

The only way to know whether an embedder is useful for *your* corpus is to look at
neighbours and judge them:

```python
embedder = HashingEmbedder()
vectors = embedder.embed(["refund policy", "refund policy", "lab access"])
print(vectors[0] @ vectors[1])   # ~1.0, identical text
print(vectors[0] @ vectors[2])   # lower, unrelated text
```

Then a harder test: take a real question from your set and print the top three chunks
with their texts, not only their scores. If the right passage is not there, no threshold
will save the system.

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Everything looks similar (scores 0.8-1.0) | Hashing collisions, or comparing unnormalised vectors | Check normalisation; raise `dim` |
| Paraphrases never match | Using a lexical embedder for a semantic task | Print the neighbours; try the trained model |
| Scores differ between runs | Text changed, or a non-deterministic model | Confirm inputs and pinned weights |
| `ImportError` for sentence-transformers | Optional stack missing | Install `requirements/llm.txt`, or stay offline |
| Similar chunks ranked oddly | Duplicate or near-duplicate chunks | Deduplicate the corpus (Module 10) |

## Checkpoint

- [ ] You can explain cosine similarity without using the word "distance" alone.
- [ ] You can state what `HashingEmbedder` captures and what it misses.
- [ ] You can point to a measured case where a high score was misleading.
- [ ] You can name one reason to prefer the trained embedder despite the download.

## Next step

Read [CA10 - Chunking, document parsing, and metadata](ca10-chunking.md). Chunking
decides what can be retrieved at all; no embedder fixes a bad split.
