# Notebook coverage audit

Audit date: **2026-11-09**. Scope: every `.ipynb` under `notebooks/`, its stored
outputs, its instructional structure, and its reachability from the built site.
Branch: `release/v0.1.0-rc.1`, commit `c6410ac`.

## Verdict

**PASS with documented limitations.** All 26 notebooks are valid JSON, contain
executed code, store no error outputs, are linked from the navigation and the
Notebook Library, and re-execute top-to-bottom on a fresh CPU kernel. **Six**
notebooks meet the exact named 14-section template. The other **20** are real,
executed instructional notebooks with a more compact legacy structure; they are
not empty, outline-only, or code-only documents.

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

F02 is `notebooks/foundations/m01_environment_check.ipynb`; the filename follows
the environment-check unit rather than a separate F02 filename.

## Execution gate

Command:

```bash
python scripts/check_notebooks.py --execute --timeout 300
```

Result after the Markdown repair:

```text
ok: 26 notebooks are valid JSON, executed, and free of stored errors
executing 26 notebooks with a 300s per-cell timeout
...
ok: executed 26 notebooks, 223 code cells in 152.6s
```

Each notebook ran in its own directory with a fresh `python3` kernel. The check
did not write modified notebooks back to disk. The run used Windows 11, Python
3.12.10, CPU only.

## Markdown rendering repair

Seven section notebooks had every Markdown prose paragraph prefixed with `# `;
headings were also double-prefixed, for example `# ## Learning objectives`. The
rendered page therefore showed body text as H1 headings.

| Notebook | Repair | Code and outputs |
| --- | --- | --- |
| `notebooks/model-training/m04_training_from_scratch.ipynb` | Prefix removed; headings normalized | Verified unchanged |
| `notebooks/model-training/m05_data_engineering.ipynb` | Prefix removed; headings normalized | Verified unchanged |
| `notebooks/llm-fine-tuning/m06_transformers.ipynb` | Prefix removed; headings normalized | Verified unchanged |
| `notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb` | Prefix removed; headings normalized | Verified unchanged |
| `notebooks/llm-fine-tuning/m08_lora_qlora.ipynb` | Prefix removed; headings normalized | Verified unchanged |
| `notebooks/ai-agents/m15_agents.ipynb` | Prefix removed; headings normalized | Verified unchanged |
| `notebooks/production/m16_production.ipynb` | Prefix removed; headings normalized | Verified unchanged |

No execution result was fabricated or rewritten. The 152.6 s run above is the
post-repair evidence.

## Instructional structure

The six notebooks that meet the full named-section standard are M09-M14:

- M09 `chatbots-rag/m09_chatbots.ipynb`
- M10 `chatbots-rag/m10_rag.ipynb`
- M11 `computer-vision/m11_image_classification.ipynb`
- M12 `computer-vision/m12_object_detection.ipynb`
- M13 `speech-audio/m13_speech_audio.ipynb`
- M14 `video-ai/m14_video_ai.ipynb`

Each contains learning objectives, prerequisites, conceptual explanation,
terminology, step-by-step code, code explanation, expected output, interpretation,
practical exercises, a challenge, limitations, common mistakes and
troubleshooting, summary, and further reading. The inventory checker enforces
those named sections for this set.

The other 20 notebooks are the 13 foundation notebooks plus M04-M08, M15, and
M16. They contain explanatory Markdown, executable code, stored outputs, and
"check your work", validation, or exercises sections, but they do not repeat every
named section. M15 and M16 include objectives, practice, common mistakes,
knowledge checks, lab connection, and further reading; M04-M08 have objectives
and a validation/exercises section but omit some of the exact headings.

This distinction is deliberate and reported rather than hidden. Adding fourteen
headings to every old notebook without new teaching content would satisfy a
checker while making the course worse; the honest status is **6 of 26 exact, 26
of 26 substantive and executable**.

## Coverage limitations

- **No GPU or Colab execution.** All 26 notebooks were run on CPU. GPU branches,
  optional pretrained-model paths, and Colab sessions are documented but
  unverified. This is material for M07-M08 and the vision/video sections.
- **Synthetic data.** Many notebooks use generated fixtures. A high score is a
  pipeline diagnostic, not a real-world benchmark.
- **No human review of learning quality.** Structural checks cannot prove that a
  beginner understands a notebook.
- **No public site check.** The built site is local; GitHub Pages is 404.
- **Notebook execution is not a deployment test.** It does not prove the public
  site, search, or mobile navigation works.

## Related evidence

- [Repository content audit](repository-content-audit.md) for the full inventory.
- [Navigation and link audit](navigation-and-link-audit.md) for reachability.
- [Student usability audit](student-usability-audit.md) for the static journeys.
- [Final audit](final-audit.md) for the overall release status.
