# Notebook coverage audit

Audit date: **2026-11-08**. Scope: every `.ipynb` under `notebooks/`, its stored
outputs, its instructional sections, and its links from the course site.

## Verdict

**PASS with documented limitations.** All 26 notebooks are valid JSON, contain
executed code cells, store no error outputs, are reachable from the site, and
execute top-to-bottom on a fresh CPU kernel. The 20 legacy notebooks do not all
follow the newer 14-section instructional template; M09-M14 do.

## Library

| Area | Notebooks | Count | Execution |
| --- | --- | ---: | --- |
| Foundations | F01, F03-F13 | 12 | Pass |
| M01 environment | `m01_environment_check` | 1 | Pass |
| Model training | M04-M05 | 2 | Pass |
| LLM fine-tuning | M06-M08 | 3 | Pass |
| Chatbots and RAG | M09-M10 | 2 | Pass |
| Computer vision | M11-M12 | 2 | Pass |
| Speech and audio | M13 | 1 | Pass |
| Video AI | M14 | 1 | Pass |
| AI agents | M15 | 1 | Pass |
| Production | M16 | 1 | Pass |
| **Total** | | **26** | **Pass** |

F02 is `notebooks/foundations/m01_environment_check.ipynb`; the numbering follows
the course sequence rather than a separate F02 filename.

## Execution gate

Command:

```bash
python scripts/check_notebooks.py --execute --timeout 300
```

Result:

```text
ok: 26 notebooks are valid JSON, executed, and free of stored errors
executing 26 notebooks with a 300s per-cell timeout
...
ok: executed 26 notebooks, 223 code cells in 176.1s
```

Every notebook ran in its own directory with a fresh `python3` kernel.
Nothing was written back during the check. The six newly added notebooks and
their cells were:

| Notebook | Code cells | Execution |
| --- | ---: | --- |
| `m09_chatbots.ipynb` | 7 | Pass |
| `m10_rag.ipynb` | 7 | Pass |
| `m11_image_classification.ipynb` | 10 | Pass |
| `m12_object_detection.ipynb` | 9 | Pass |
| `m13_speech_audio.ipynb` | 11 | Pass |
| `m14_video_ai.ipynb` | 10 | Pass |

The executable M09-M14 notebooks are in the
[Notebook Library](../notebook-library.md), and their lessons are linked from the
section indexes.

## M09-M14 instructional review

Each of the six applied notebooks contains:

- learning objectives and prerequisites;
- conceptual explanation and terminology;
- step-by-step implementation with code explanations;
- stored execution output and interpretation;
- practical exercises and a challenge;
- limitations and troubleshooting;
- summary and further reading.

The inventory checker enforces these fourteen named sections:
learning objectives, prerequisites, conceptual explanation, terminology,
explanation of the code, expected output, interpretation, practical exercises,
challenge, limitations, common mistakes, troubleshooting, summary, and further
reading.

## Reproducibility checks

M11 and M12 were re-executed in a separate fresh kernel and their reported
metrics were compared with the stored outputs.

| Notebook | Stored and reproduced result |
| --- | --- |
| M11 image classification | Test accuracy **0.867**; majority baseline **0.40**; 39 of 45 test images correct |
| M12 object detection | mAP@0.5 **0.169**; per-class AP circle **0.381**, square **0.042**, triangle **0.083**; precision **0.073**, recall **0.429** |

M11 explains that 0.867 is above the 0.40 baseline but still has a weak class and
is not a benchmark result. M12 states plainly that 0.169 is a weak
precision-recall result, that 82 predicted boxes were produced for 59
ground-truth objects, and that the notebook is a teaching baseline rather than a
production detector. Both notebooks now include an explicit Limitations section.

## Coverage limitations

- The earlier 20 notebooks were authored before the 14-section standard. They
  contain real explanations, code, and outputs, but their section structure is
  not uniform.
- The six applied notebooks use synthetic data. Perfect or near-perfect scores
  on synthetic fixtures are pipeline diagnostics, not evidence of real-world
  accuracy.
- GPU and Colab execution remain unverified; the checked path is CPU-only.
- The inventory gate checks structure and execution, not pedagogical quality.
  Human review and a student pilot are still required.
