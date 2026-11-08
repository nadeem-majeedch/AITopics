# CV12 - Image embeddings and similarity search {#cv12}

**Section path:** [Overview](index.md) · **Module 12** · [Lab 7](labs/lab7-similarity-app.md) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | CV06 (embeddings from a trunk), CA09 (the text version of the same idea) |
| **You will produce** | Two indexes over the same gallery, their precision@k, and a one-paragraph explanation of the difference |

## Why this module exists

"Find similar images" is the least specified feature in computer vision. Similar by what

- colour, shape, texture, object identity, or scene? An embedding is a *choice* of what
  counts as similar, and the only way to know whether the choice is right is to measure
  retrieval quality on labelled data.

This module builds two embeddings for the same images - a colour histogram and a learned
CNN feature - and compares them with precision@k. One number separates them, and the
disagreement between them is the lesson.

## What an embedding is here

```python
vector = similarity.histogram_embedding(image)     # 96-d, L2-normalised
vector = transfer.extract_features(model, images, mean, std)   # 64-d from TinyCNN.features
```

A fixed-length vector per image, L2-normalised so that the dot product *is* cosine
similarity. Normalising once at index time, not per query, is why search is a matrix
multiply:

```python
index = similarity.EmbeddingIndex.from_records(gallery_records)
hits = index.search(similarity.histogram_embedding(query.image), k=5)
print(similarity.format_hits(hits, datasets.OBJECT_CLASSES))
```

```text
rank  score   label     source
   1  0.9663  bottle    obj-1-5
   2  0.9663  bottle    obj-1-5
   3  0.9662  bottle    obj-1-5
```

Note the duplicate sources: variants of one object dominate the top-k. That is correct
behaviour for "find similar" and a problem for "find *other* similar products". Which one
you want is a product decision, and it changes the evaluation.

## precision@k, and the two ways to compute it

```python
row = index.precision_at_k(query_records, k=5, exclude_self=True)
# {'precision_at_k': 0.4, 'k': 5, 'n_queries': 18, ...}
```

Precision@k is the fraction of the top-k results that share the query's label.

The subtlety: if a query is *inside* the index, it returns itself first, which inflates
precision by construction. With disjoint gallery and query sets the flag changes nothing,
and this section's data is disjoint (84 gallery, 18 queries):

| Embedding | precision@5, self included | precision@5, self excluded | 1-NN accuracy |
| --- | --- | --- | --- |
| Colour histogram | 0.400 | 0.400 | 0.500 |
| Learned CNN features | - | **0.589** | - |

The equality is the honest result: the flag was irrelevant because the sets do not
overlap. If you index your whole dataset and then query it, self-inclusion will dominate
and you will report a number that means nothing.

## Why the numbers are what they are

Four classes (`bottle`, `mug`, `ball`, `book`) rendered with different shapes and colours.
A colour histogram groups by palette, not by object, so:
- two objects with the same palette look similar regardless of shape,
- precision@5 of 0.400 is barely above the 0.25 chance level,
- 1-NN accuracy of 0.500 means half the nearest neighbours are the right class.

The learned features do better (0.589) because they were trained to separate these
classes - an embedding inherits the task it was trained for. That is the central insight:
**there is no general-purpose image embedding, only one aligned to some objective.**

## Indexing: what changes at scale

Brute force is a matrix multiply and is exact:

```text
scores = embeddings @ query            # (N, d) @ (d,) -> (N,)
top_k  = np.argpartition(-scores, k)[:k]
```

Cost grows linearly in `N`. At 84 images this is free; at 10 million it is not, and you
move to approximate nearest neighbour (HNSW, IVF-PQ) and accept a recall loss you must
measure. The section deliberately stops at exact search: approximate indexing without a
measured recall@k is a way to be fast and wrong.

Three practical rules:

1. **Version the embedding model with the index.** Re-embedding with a new model
   invalidates every stored vector; mixing them produces nonsense similarities.
2. **Store the label and source id next to the vector**, so evaluation and deduplication
   are possible later.
3. **Deduplicate before you evaluate.** Variants of one source fill the top-k and hide
   whether the model generalises.

## Evaluation that matches the use case

| Use case | Metric | Note |
| --- | --- | --- |
| "More like this" | precision@k, human-judged | labels may not capture "similar" |
| Product deduplication | recall@k of true duplicates | need a duplicate ground truth |
| Reverse image search | rank-1 / mAP@k | gallery is huge, false matches matter |
| Clustering / exploration | silhouette, visual inspection | no labels |

```python
similarity.nearest_neighbour_accuracy(index, query_records)   # cheap, coarse
```

## Practice

1. Build both indexes over the same gallery and report precision@5 and 1-NN accuracy.
2. Index the gallery *and* the queries together, then re-run with `exclude_self=False`.
   Show the inflation and explain it.
3. Add a fifth class with a palette already used by another class. Report the effect on
   the colour embedding and on the learned one.
4. Pick three queries where the two embeddings disagree and describe what each one
   considered "similar".

## Check yourself

1. Why is precision@k meaningless if the query is in the index and self-matches are counted?
2. Your colour embedding scores 0.40 and your CNN 0.589. Which do you ship, and what
   else do you need to know before deciding?
3. You re-embed half the gallery with a new model. What breaks, and how would you have
   prevented it?

## What comes next

[CV13](cv13-optimization-and-inference.md) asks what it costs to run any of this: latency,
memory, threads, batch size, and whether quantisation is worth it.
