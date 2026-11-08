# Lab 7 - Build a simple image similarity application

**Section path:** [Overview](../index.md) · Module [CV12](../cv12-embeddings-and-similarity.md) · **Lab 7** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only |
| **Code** | `projects/computer-vision/lab7_similarity.py` |
| **Prerequisite** | Lab 4 (for the learned embedding), CV12 |

## The task

Build a "find similar images" index over a gallery, answer queries with ranked results,
and evaluate retrieval with precision@k using **two different embeddings**. Then explain
why they disagree.

Deliverables:

1. an index of 84 gallery images with a 96-d colour embedding,
2. ranked results for a query, with labels and source ids,
3. precision@5 and 1-NN accuracy for the colour embedding,
4. the same metrics for a learned CNN embedding, and a written comparison.

## Setup

```bash
python scripts/make_vision_data.py
cd projects/computer-vision
python lab4_finetune_objects.py        # optional: provides the learned embedding
python lab7_similarity.py
```

Gallery: 84 images, 18 queries, four classes (bottle, mug, ball, book), grouped by source
so a query's own variants can be in the gallery but the *source* never crosses.

## Run it

```bash
python lab7_similarity.py --query 0 --k 5
```

Verified output:

```text
gallery 84 images  queries 18  k 5
classes ('bottle', 'mug', 'ball', 'book')
index: 84 vectors, dim 96

=== nearest neighbours for query 0
rank  score     label     source
   1  0.9663    bottle    obj-1-5
   2  0.9663    bottle    obj-1-5
   3  0.9662    bottle    obj-1-5
   4  0.9641    bottle    obj-1-1
   5  0.9636    mug       obj-1-12
query label: bottle

=== precision@k on the colour embedding
self included : precision@5 0.400  (n=18)
self excluded : precision@5 0.400  (n=18)
1-NN accuracy : 0.500

learned CNN embedding: precision@5 0.589
compare it with the colour embedding: different notion of 'similar'

report: .../outputs/lab7_similarity.json
0 failure(s)
PASS  index built, queries answered, precision measured
```

## Reading the results

1. **Top results are variants of one source.** Three of the five hits share `obj-1-5`. For
   "more like this" that is correct; for "other similar products" it is wrong. The product
   decides which evaluation you need.
2. **Colour embedding: 0.400 vs chance 0.250.** A colour histogram groups by palette, not
   by object. Half the nearest neighbours are the right class.
3. **Self inclusion changed nothing** (0.400 both ways) because gallery and queries are
   disjoint. If you index everything and query it, self-matches inflate precision and the
   number becomes meaningless.
4. **Learned features: 0.589.** Better, because they were trained to separate these
   classes. An embedding inherits its training objective - there is no general "similar".

## Test cases

| Check | Expected | Verification |
| --- | --- | --- |
| Index size | 84 vectors x 96 dims | printed |
| Hit count | equals `--k` | printed table |
| Scores descending | yes | table |
| Unit norm | ||v|| = 1 for embeddings | assert in code |
| precision@k in [0, 1] | yes | printed |
| Self-exclusion flag works | identical when disjoint; differs when overlap | run both modes |
| JSON written | valid, both embeddings | `lab7_similarity.json` |

```bash
python -m unittest tests.test_computer_vision.TestSimilarityAndDeployment -v
```

## Rubric

| Criterion | Marks | What earns full marks |
| --- | --- | --- |
| Working index and query | 20 | ranked output with labels and sources |
| Correct evaluation | 25 | precision@k and 1-NN with N stated; self-match semantics explained |
| Second embedding | 20 | learned embedding measured on the same split |
| Comparison | 25 | explains *why* they differ, in terms of what each embeds |
| Product framing | 10 | names a use case and says which evaluation it needs |

## Extensions

1. Add a fifth class sharing a palette with an existing one. Report both embeddings.
2. Index gallery + queries together and compare `exclude_self` True/False. Quantify inflation.
3. Replace cosine with L2 distance. Does the ranking change?
4. Build a "near-duplicate detector" using `dhash` and compare its precision with the
   colour index on the same queries.

## Submit

```text
cv-lab7/
  README.md
  results.md         # ranked queries, both embeddings, metrics
  analysis.md        # why they disagree, which you would ship, and why
  lab7_similarity.json
```

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| precision@k = 1.000 suspiciously | query indexed with itself | use disjoint sets or `exclude_self=True` |
| All scores identical | embeddings not normalised, or constant image | normalise; check input variance |
| No learned comparison | Lab 4 checkpoint missing | run Lab 4 first |
