"""Lab 7 - Build a simple image similarity application.

Two embedders, one index:

* a colour-histogram + thumbnail embedding (no training);
* a CNN feature embedding, if a trained checkpoint is available.

The comparison is the lesson: the hand-built embedding groups images by palette,
the learned one groups them by shape. Neither is "correct" - which one you want
depends on the query, and the lab makes you say which and why.

Run:

    python lab7_similarity.py
    python lab7_similarity.py --query 0
    python lab7_similarity.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from vision_core import datasets, dataio, models, similarity, training, transfer

OUTPUTS = Path(__file__).resolve().parent / "outputs"


def object_records(seed: int = 1):
    records = datasets.make_object_dataset(n_sources=40, size=32, seed=seed, variants_per_source=3)
    return datasets.group_split(records, seed=seed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", type=int, default=0)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    splits = object_records()
    gallery_records = splits["train"]
    query_records = splits["test"]
    print(f"gallery {len(gallery_records)} images  queries {len(query_records)}  k {args.k}")
    print(f"classes {datasets.OBJECT_CLASSES}")

    index = similarity.EmbeddingIndex.from_records(gallery_records)
    print(f"index: {len(index)} vectors, dim {index.embeddings.shape[1]}")

    print(f"\n=== nearest neighbours for query {args.query}")
    query = query_records[args.query]
    hits = index.search(similarity.histogram_embedding(query.image), k=args.k)
    print(similarity.format_hits(hits, datasets.OBJECT_CLASSES))
    print(f"query label: {datasets.OBJECT_CLASSES[query.label]}")

    print("\n=== precision@k on the colour embedding")
    with_self = index.precision_at_k(query_records, k=args.k, exclude_self=False)
    without_self = index.precision_at_k(query_records, k=args.k, exclude_self=True)
    print(f"self included : precision@{args.k} {with_self['precision_at_k']:.3f}  (n={with_self['n_queries']})")
    print(f"self excluded : precision@{args.k} {without_self['precision_at_k']:.3f}  (n={without_self['n_queries']})")
    print(f"1-NN accuracy : {similarity.nearest_neighbour_accuracy(index, query_records):.3f}")

    learned = None
    checkpoint = OUTPUTS / "lab4_objects.pt"
    if checkpoint.exists():
        model = models.TinyCNN(num_classes=len(datasets.OBJECT_CLASSES), width=16)
        models.load_checkpoint(model, checkpoint)
        gallery_images = np.stack([r.image for r in gallery_records])
        query_images = np.stack([r.image for r in query_records])
        mean, std = training.dataset_stats(gallery_images)
        gallery_vectors = transfer.extract_features(model, gallery_images, mean, std)
        query_vectors = transfer.extract_features(model, query_images, mean, std)
        learned_index = similarity.EmbeddingIndex.from_vectors(
            gallery_vectors,
            [r.label for r in gallery_records],
            [r.source_id for r in gallery_records],
        )
        learned = learned_index.precision_at_k(query_records, k=args.k, embedder=lambda img: _cnn_embed(model, img, mean, std))
        print(f"\nlearned CNN embedding: precision@{args.k} {learned['precision_at_k']:.3f}")
        print("compare it with the colour embedding: different notion of 'similar'")
    else:
        print("\n(no lab4 checkpoint; run lab4_finetune_objects.py to compare a learned embedding)")

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS / "lab7_similarity.json"
    path.write_text(
        json.dumps(
            {
                "k": args.k,
                "gallery": len(gallery_records),
                "queries": len(query_records),
                "precision_self_included": with_self,
                "precision_self_excluded": without_self,
                "nearest_neighbour_accuracy": similarity.nearest_neighbour_accuracy(index, query_records),
                "learned_precision": learned,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\nreport: {path}")

    failures = 0
    if without_self["precision_at_k"] > 1.0 or without_self["precision_at_k"] < 0.0:
        print("FAIL  precision outside 0-1")
        failures += 1
    if without_self["n_queries"] != len(query_records):
        print("FAIL  some queries returned no results")
        failures += 1
    if args.selftest and without_self["precision_at_k"] < 0.25:
        print(f"FAIL  precision@{args.k} {without_self['precision_at_k']:.3f} below the 0.25 floor")
        failures += 1

    print(f"\n{failures} failure(s)")
    if failures == 0:
        print("PASS  index built, queries answered, precision measured")
    return 0 if failures == 0 else 1


def _cnn_embed(model, image: np.ndarray, mean, std) -> np.ndarray:
    """CNN feature vector for one image, normalized like the gallery."""
    vector = transfer.extract_features(model, image[None, ...], mean, std)[0]
    return vector / max(1e-6, float(np.linalg.norm(vector)))


if __name__ == "__main__":
    raise SystemExit(main())
