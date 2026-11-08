# Repository content audit

Audit date: **2026-11-08**. Branch: `release/v0.1.0-rc.1`. Base commit:
`5fdf5de`. This audit checks files on disk, not claims in the README or the
curriculum map.

## Verdict

**The local course content is complete enough for deployment review.** Every
advertised module has lesson files, a notebook or a documented capstone
substitute, practical work, and an assessment. No advertised notebook directory
is empty, and every notebook is linked from both the MkDocs navigation and the
Notebook Library.

This is not a claim that the public course is live. GitHub Pages remains
unpublished, and no human student pilot has been completed.

## Verified inventory

Measured by `python scripts/check_course_inventory.py`:

| Item | Verified count |
| --- | ---: |
| Modules M00-M17 | 18 |
| Module lesson files | 105 |
| Executable notebooks | 26 |
| Labs and project briefs | 52 |
| Assessments | 21 |
| Notebooks meeting the full 14-section standard | 6 |

The 26 notebooks comprise 13 foundation notebooks and 13 section notebooks.
The six new applied notebooks are M09-M14:

- `notebooks/chatbots-rag/m09_chatbots.ipynb`
- `notebooks/chatbots-rag/m10_rag.ipynb`
- `notebooks/computer-vision/m11_image_classification.ipynb`
- `notebooks/computer-vision/m12_object_detection.ipynb`
- `notebooks/speech-audio/m13_speech_audio.ipynb`
- `notebooks/video-ai/m14_video_ai.ipynb`

## What changed in this pass

- Added the six missing applied notebooks and executed them top-to-bottom.
- Added `docs/notebook-library.md` with a direct link to every notebook.
- Added all 26 notebooks to `mkdocs.yml`, mounted through `mkdocs-jupyter`.
- Added `scripts/check_course_inventory.py` as a gate for module lessons,
  notebooks, labs, assessments, executed outputs, and the 14-section standard.
- Removed the remaining `.gitkeep` placeholders from notebook directories.
- Added direct notebook links to section indexes, foundation notebook guides,
  the lessons index, the curriculum-coverage map, and the content inventory.
- Fixed the deterministic chatbot/RAG regression described in the
  [Final audit](final-audit.md) and the [Release-readiness audit](release-readiness-audit.md).

## Content evidence

The six new notebooks were executed with a fresh CPU kernel. Their measured
anchors are recorded in the notebook outputs and in the
[Notebook coverage audit](notebook-coverage-audit.md):

- M09: cited FAQ retrieval, bounded history, injection quarantine, and redaction.
- M10: grounded registration answer with a real citation, fabricated citation
  rejection, and configured abstention.
- M11: 0.867 test accuracy against a 0.40 majority baseline on synthetic shapes.
- M12: mAP@0.5 0.169, precision 0.073, recall 0.429; explicitly reported as a
  teaching baseline, not a production detector.
- M13: clean and distorted audio evaluation, speaker EER, and CTC mechanics.
- M14: simulated traffic counting with MOTA and tracker throughput.

## Limitations

- The 20 pre-existing notebooks retain their original instructional structure.
  Only M09-M14 contain the full 14-section standard enforced by the inventory
  checker.
- All execution evidence is local Windows 11 CPU. GPU branches and Google Colab
  were not executed.
- The applied datasets are synthetic. Their metrics demonstrate pipelines and
  evaluation logic, not real-world model quality.
- GitHub Pages has not been deployed, so public navigation is not verified.
- No human student completed the course or the capstone during this audit.

## Gates run

| Gate | Result |
| --- | --- |
| Course inventory | PASS: 18 modules, 105 lesson files, 26 notebooks, 52 labs, 21 assessments |
| Notebook JSON and stored outputs | PASS: 26 notebooks valid, executed, no stored errors |
| Full notebook execution | PASS: 26 notebooks, 223 code cells, 176.1 s |
| Source Markdown links and anchors | PASS |
| Strict MkDocs build | PASS |
| Built-site links and `/AITopics` prefix | PASS |
| Licensing validator | PASS |

Exact commands and final counts are repeated in the
[Navigation and link audit](navigation-and-link-audit.md) and the
[Final audit](final-audit.md).
