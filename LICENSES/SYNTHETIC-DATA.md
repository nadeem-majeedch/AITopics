# Synthetic dataset provenance and CC0 record

This is the tracked provenance record for original synthetic datasets generated
by AITopics code. It supports the CC0 1.0 dedication in
[`CC0-1.0.txt`](CC0-1.0.txt). The generated data directories themselves are
git-ignored and are not modified by this record.

## Dedication

To the extent that **Muhammad Nadeem Majeed** owns copyright or database rights
in the original synthetic datasets listed below, those datasets are dedicated to
the public domain under **CC0 1.0 Universal**. The full legal text is in
[`CC0-1.0.txt`](CC0-1.0.txt). No attribution is required by CC0; citation of
AITopics and the generator is encouraged so that users understand the data is
synthetic.

This dedication does **not** cover third-party datasets, downloaded media,
pretrained model weights, or model checkpoints derived from third-party weights.

## Provenance verification

Each generator was inspected for the licensing review on **2026-11-07**. The
review confirmed that the generators:

- use fixed random seeds and standard-library/NumPy primitives;
- do not download data or call a network service;
- do not read third-party images, audio, video, or text as source material; and
- emit synthetic records, images, audio, or documents written for the course.

The generated dataset cards repeat the CC0-1.0 label and state that no real
people or third-party content are included. This is a provenance review of the
repository's generators, not a copyright audit of every possible output.

## Covered datasets

| Generator | Output (git-ignored unless noted) | CC0 record |
| --- | --- | --- |
| `scripts/make_foundation_data.py` | `datasets/foundations/generated/` | Generator and dataset card declare CC0-1.0; no real people or third-party rows. |
| `scripts/make_training_data.py` | `datasets/training/generated/` | Manifest declares `"license": "CC0-1.0"`; no scraped or third-party text. |
| `scripts/make_chatbot_data.py` | `data/chatbots-rag/` | Fictional Study Hub corpus; no private documents, downloads, or real people. |
| `scripts/make_agent_data.py` | `data/agents/` | Manifest/README declare CC0-1.0; synthetic handbooks, CSVs, and tasks. |
| `scripts/make_capstone_data.py` | `data/capstones/` | Dataset cards declare CC0-1.0; template-generated tickets and instructions. |
| `scripts/make_eval_data.py` | `data/production/` | Fictional customers, clinic handbook, detector ground truth, and attacks; no real people. |
| `scripts/make_audio_data.py` | `data/audio/` | Dataset card declares CC0-1.0; every clip is synthesised; no real recordings. |
| `scripts/make_vision_data.py` | `data/computer-vision/` | Dataset card declares CC0-1.0; images rendered from NumPy primitives; no scrape/download. |
| `projects/video-ai/scripts/make_video_data.py` | `projects/video-ai/data/` | Dataset card declares CC0-1.0; synthetic traffic clip with frame-exact ground truth. |

## P06 object dataset

| Field | Record |
| --- | --- |
| Dataset | `objects_p06` v1.0.0 |
| Location | `data/computer-vision/objects_p06/` (git-ignored generated output) |
| Generator | `scripts/make_vision_data.py` |
| Images | 960 synthetic object images in stratified train/val/test splits |
| Source material | NumPy primitives rendered by repository code |
| Third-party images | None |
| Real people | None |
| Dataset card | `data/computer-vision/dataset_card.json` records `CC0-1.0 (public domain dedication)` and states that no third-party images are included |
| Integrity record | `manifest.json` records SHA-256 for every image; `python scripts/make_vision_data.py --check` verifies it |
| Historical results | The original P06 set and the separate deduplicated/balanced experimental sets are unchanged; this record adds licensing metadata only |

The 57 same-split duplicate groups reported by the integrity check are generated
variants, not third-party copies. Duplicate content does not change the CC0
provenance analysis.

## What is not covered

- COCO, CIFAR-10, DeepFashion, or any student-supplied dataset.
- SmolLM2, Qwen, torchvision SSDLite COCO weights, or other pretrained weights.
- Fine-tuned checkpoints derived from third-party weights.
- Any future asset whose generator reads an external file or downloads content
  without a separate provenance and licence review.

If a new synthetic dataset is added, update this record and
[`licensing-scope.json`](../licensing-scope.json) before distributing it under
CC0.
