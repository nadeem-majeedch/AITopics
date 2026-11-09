# Final repository audit

Audit date: **2026-11-09**. Scope: the whole repository after the navigation,
resources, notebook-rendering, and publication-workflow repair pass. This page
records what exists, what was executed, what passed, and what remains limited. It
is maintainer documentation; students do not need it.

For the current release decision, CI evidence, and licensing register, see the
[Release-readiness audit](release-readiness-audit.md) and the
[Licensing and attribution register](licensing-and-attribution.md).

## Executive verdict

**READY WITH DOCUMENTED LIMITATIONS.** The local course is coherent, navigable,
verified by its automated gates, and ready for the release owner to push and
deploy. It is **not** yet verified as a public student course.

Every required local gate passes on this tree: 269 unit tests, 26 notebook JSON
checks, 26 fresh-kernel notebook executions (223 code cells, 262.4 s), course
inventory, source and built-site links, strict MkDocs (323 pages), licensing (572
release files), workflow schemas, and whitespace. The remaining limitations are
environmental and evidentiary:

* GitHub Pages is still unpublished: the Pages API and project URL both return
  HTTP 404, and no validation/deployment workflow has run on GitHub Actions;
* no notebook was executed on a GPU, and no Google Colab session was run;
* the optional Hugging Face/bitsandbytes path in M07/M08 was not executed (CPU
  only, no model download);
* the capstone was piloted by an agent through the three checkpoint gates, but no
  human student submission or human marking exists;
* only 6 of 26 notebooks (M09-M14) meet the exact named 14-section template; the
  other 20 are substantive, executed, and linked but use a more compact structure;
* the public origin, search relevance, mobile layout, and the committed
  `release/v0.1.0-rc.1` push remain unverified;
* notebook pages offer a downloadable `.ipynb`, but the repository commits no
  notebook SHA-256 manifest, so a download is verified by hashing it against the
  committed blob (`git show HEAD:<path>`) rather than a CRLF working copy (see
  [GitHub Pages publication](GITHUB-PAGES.md#release-publication-procedure-nine-steps)).

This is not a claim that students can already reach a public site. It is a claim
that the repository is ready for the push and deployment review that precedes
that step, with the limitations above made explicit.

## Release candidate snapshot

Recorded **2026-11-09** immediately before the gates below were re-run. Nothing
was committed, staged, pushed, tagged, or deployed to produce this snapshot.

| Item | Value |
| --- | --- |
| Branch | `release/v0.1.0-rc.1` (also the remote default branch) |
| Local HEAD | `c6410acbbd18af88676418ea6355395bad169e98` (`c6410ac missing notebooks add`) |
| Upstream | `origin/release/v0.1.0-rc.1` = `5fdf5dec97439753e240b4d96b8371affd287609` |
| Ahead / behind | 1 / 0 |
| Staged paths | **0** |
| Tracked changes | **59** (50 modified, 9 deleted) |
| Untracked files | **12** |
| Total status entries | **71** |
| Diff size | **59 files changed, 2,510 insertions(+), 1,570 deletions(-)** (`git diff --stat`, measured on this exact tree; it includes these documentation updates) |

### File-by-file inventory

**Created (12, untracked).** `docs/resources/index.md`;
`docs/technical/repository-inventory.json`; `labs/README.md`;
`labs/ai-agents/README.md`, `labs/chatbots-rag/README.md`,
`labs/computer-vision/README.md`, `labs/llm-fine-tuning/README.md`,
`labs/model-training/README.md`, `labs/production/README.md`,
`labs/speech-audio/README.md`, `labs/video-ai/README.md`;
`tests/test_chatbot_parser_regression.py`.

**Deleted (9).** The empty placeholders `labs/ai-agents/.gitkeep`,
`labs/chatbots-rag/.gitkeep`, `labs/computer-vision/.gitkeep`,
`labs/foundations/.gitkeep`, `labs/llm-fine-tuning/.gitkeep`,
`labs/model-training/.gitkeep`, `labs/production/.gitkeep`,
`labs/speech-audio/.gitkeep`, `labs/video-ai/.gitkeep`. Each is a zero-byte file
replaced by a substantive README or by real foundation starter files; no content
was deleted.

**Modified (50).**

| Area | Paths |
| --- | --- |
| Workflows | `.github/workflows/deploy-pages.yml`, `.github/workflows/validate-docs.yml` |
| Notebooks (Markdown-only repair) | `notebooks/model-training/m04_training_from_scratch.ipynb`, `notebooks/model-training/m05_data_engineering.ipynb`, `notebooks/llm-fine-tuning/m06_transformers.ipynb`, `notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb`, `notebooks/llm-fine-tuning/m08_lora_qlora.ipynb`, `notebooks/ai-agents/m15_agents.ipynb`, `notebooks/production/m16_production.ipynb` |
| Navigation and status | `mkdocs.yml`, `README.md`, `docs/index.md`, `docs/about/instructor.md`, `docs/course/roadmap.md`, `docs/course/learning-paths.md`, `docs/course/assessments/index.md`, `docs/syllabus/index.md`, `docs/syllabus/level-0-start.md`, `docs/syllabus/level-1-foundations.md`, `docs/syllabus/level-2-language.md`, `docs/syllabus/level-3-vision-video.md`, `docs/syllabus/level-4-agents.md`, `docs/syllabus/level-5-production.md`, `docs/planning/content-inventory.md`, `docs/planning/curriculum-coverage.md`, `docs/planning/repository-architecture.md` |
| Video and robot lessons | `docs/lessons/video-ai/governance.md`, `docs/lessons/video-ai/index.md`, `docs/lessons/video-ai/model-card.md`, `docs/lessons/video-ai/vd15-responsible-video-analytics.md`, `docs/lessons/video-ai/labs/lab-1-preprocessing.md` |
| Chatbot lesson (pre-existing) | `docs/lessons/chatbots-rag/ca14-evaluation.md`, `docs/lessons/chatbots-rag/index.md` |
| Technical audits | `docs/technical/GITHUB-PAGES.md`, `docs/technical/build-and-deploy.md`, `docs/technical/contributing.md`, `docs/technical/final-audit.md`, `docs/technical/github-pages-deployment-audit.md`, `docs/technical/licensing-decision-package.md`, `docs/technical/navigation-and-link-audit.md`, `docs/technical/notebook-coverage-audit.md`, `docs/technical/release-notes-v0.1.0-rc.1.md`, `docs/technical/release-readiness-audit.md`, `docs/technical/repository-content-audit.md`, `docs/technical/student-usability-audit.md`, `docs/technical/v1-release-candidate-checklist.md` |
| Code and data instructions | `projects/chatbots-rag/chatbot_core/model_client.py`, `projects/video-ai/lab_support.py`, `requirements/video.txt`, `scripts/check_course_inventory.py` |

Review findings from the full diff pass: the nine deletions are only empty
placeholders; the seven notebook diffs change Markdown cells only, with code
sources, execution counts, and stored outputs identical to `HEAD`; the workflow
diffs widen triggers to `release/**` without granting Pages permissions to the
validation job; the `mkdocs.yml` diff adds the resources nav entry and updates
`edit_uri` while leaving `site_url` unchanged. One repair defect was found and
fixed during this review: `docs/lessons/video-ai/model-card.md` had its table
delimiter and two rows collapsed onto a single line, which broke the rendered
Data table. No other merged-line or generated-artifact defect was found; the
only new build artifact is `docs/technical/repository-inventory.json`, which is
intentionally committed as evidence.

### Snapshot verification

Measured on the working tree at `c6410ac` before this page was updated:

| Check | Result |
| --- | --- |
| Notebook source integrity | **7 modified notebooks; Markdown cells only. 0 code-cell changes, 0 output changes, 0 execution-count changes; cell counts unchanged (26/23/21/17/20/21/24)** |
| Downloadable notebook copies | **26 source notebooks, 26 copies under `site/notebooks/`; 0 SHA-256 mismatches** |
| Pre-existing parser change | **Preserved: `model_client.py`, 13 insertions, no deletion of the behaviour it adds** |
| Pre-existing regression test | **Preserved and passing: `tests/test_chatbot_parser_regression.py`, 16 tests OK** |
| Credential scan of all 71 candidate paths | **0 matches for GitHub, OpenAI-style, AWS, Slack, or private-key patterns; only `.env.example` is tracked** |
| Checkpoints and binaries | **None in the diff; no `.pt`, `.pth`, `.ckpt`, `.bin`, `.safetensors`, `.onnx`, image, or media file changed** |
| Generated build state | **`site/`, `tmp/`, `data/`, `.venv/`, `.cache/`, `outputs/`, and `__pycache__/` are ignored and untracked; none enter the candidate** |
| Whitespace | **`git diff --check` and `git diff --cached --check` both clean** |

`scripts/check_notebooks.py --execute` runs each notebook from a fresh kernel
without writing back to the source file, which the integrity check above
confirms: no stored output or execution count moved during the 262.4 s run.

## 2026-11-09 repair and revalidation

This pass did not replace valid course material. It repaired delivery and
navigation defects, then re-ran the gates against the files on disk.

| Repair | Evidence |
| --- | --- |
| Fixed accidental `# ` prose prefixes and double-prefixed headings in seven notebooks (M04-M08, M15, M16) | Code cells, stored outputs, and execution counts verified unchanged |
| Re-executed all 26 notebooks after the Markdown repair | **26 notebooks, 223 cells, 262.4 s, 0 failures** |
| Restored the video model-card table delimiter and rows that a repair had merged into one line | Table renders again; caught in the final diff review, not by any automated gate |
| Linked module names in the roadmap, learning paths, syllabus overview, and every syllabus level page | Every student-facing module entry now has a relative link |
| Linked notebook paths and lesson names in curriculum coverage and the assessment coverage map | No nonexistent targets introduced; source link checker passes |
| Added a student-facing [Datasets and Resources](../resources/index.md) page and navigation entry | Data, generator, licence, hardware, and pretrained-model guidance in one place |
| Replaced empty top-level lab placeholders with README pointers | `labs/README.md` plus eight area READMEs; obsolete `.gitkeep` files removed |
| Corrected the video-data generator path in seven lesson references, `lab_support.py`, and `requirements/video.txt` | Real path is `projects/video-ai/scripts/make_video_data.py` |
| Added resource reachability and structural floors to `scripts/check_course_inventory.py`; added JSON output | `docs/technical/repository-inventory.json` |
| Made the Pages deployment workflow selectable from the actual release branch | `workflow_run.branches` now includes `main` and `release/**`; `edit_uri` points at the current branch |
| Rebuilt and rechecked the site | **296 source Markdown files; 323 built pages; 0 broken links; 0 prefix violations** |

### Final repair-pass gate table

| Gate | Result |
| --- | --- |
| Full unit suite | **269 tests, OK** |
| Notebook JSON and stored outputs | **26 valid, executed, 0 stored errors** |
| Notebook execution | **26 notebooks, 223 code cells, 262.4 s** |
| Course inventory | **18 modules, 105 unique lesson files, 26 notebooks, 52 unique labs/project briefs, 21 unique assessments; 18 complete, 0 partial, 0 missing** |
| Broken links before / after | **0 / 0** in the internal checker; the navigation defect was unlinked table entries, not dead hrefs |
| Source Markdown links and anchors | **296 files, 0 broken** |
| Strict MkDocs build | **0 warnings, 323 built pages** |
| Built-site links and `/AITopics` prefix | **PASS: 323 pages** |
| Licensing | **PASS: 8 checks, 572 release files classified** |
| Workflow schemas | **PASS: two workflows and Dependabot config validate against their published schemas** |
| Whitespace | **`git diff --check` clean** |
| GitHub Pages | **HTTP 404; not deployed** |
| GitHub Actions validation/deploy | **No run found; 2 Dependabot runs only** |

Required totals: **18 modules; 105 expected / 105 existing lesson files; 26
expected / 26 existing notebooks; 52 expected / 52 existing labs and project
briefs; 21 expected / 21 existing assessments; 0 missing in every category.**
The previous 2026-11-08 pass remains below as historical evidence. Its 159.3 s
notebook timing and 295/322 page counts were superseded by the re-run above.

## Previous repair and validation pass (2026-11-08)

### Chatbot/RAG regression

The full unit suite initially reported **2 failures out of 253**:
`test_rag_missing_document_abstains` and
`test_rag_irrelevant_retrieval_is_not_used_as_evidence`. Both are required RAG
quality cases, so this blocked the release.

Root cause: the deterministic `FakeModelClient` parser had been corrected to stop
treating the user-turn instruction paragraph (`Reply with the JSON object...`) as
part of the question. That correction exposed a weaker support rule: one shared
content word (for example, `workshop` or `much`) was enough to claim an answer.
Before the parser fix, instruction words diluted the overlap ratio and masked the
defect; the tests passed for the wrong reason.

Fix in `projects/chatbots-rag/chatbot_core/model_client.py`:

- preserve the evidence header (title and section) separately from the body;
- decide support against the header plus body, not just one sentence;
- require two matching content words, except for a one-word question whose whole
  content is present;
- require the selected answer sentence (or its heading context) to carry enough
  of the question to avoid answering a different fact from a merely related page;
- keep sentence-level extraction for the returned answer and keep the JSON
  response contract unchanged.

No test was weakened, skipped, deleted, or rewritten. The two failing tests pass,
and `tests/test_chatbot_parser_regression.py` adds **16** behaviour-level cases
covering instruction separation, weak overlap, title/section/body support,
abstention, one-word questions, citations, and malformed output. The complete
suite is **269 tests, OK**.

The 14-question dev evaluation reports answer accuracy 1.0, abstention
correctness 1.0, citation precision 1.0, recall 1.0, and hit@k 1.0. The separate
held-out 12-question test set reports answer accuracy 0.75 (three misses:
t05, t06, t07); that is a documented lexical-client limitation, not a passing
claim for the test split.

### Notebook and site completion

Six applied notebooks were added and executed: M09 chatbots, M10 RAG, M11 image
classification, M12 object detection, M13 speech/audio, and M14 video AI. The
Notebook Library and MkDocs navigation now link all 26 notebooks. The six new
notebooks were each rechecked for the 14-section instructional standard, including
explicit limitations and troubleshooting.

### Previous measured results (2026-11-08)

| Gate | Result |
| --- | --- |
| Full unit suite | **269 tests, OK** |
| Notebook JSON and stored outputs | **26 notebooks valid, 0 errors** |
| Notebook execution | **26 notebooks, 223 code cells, 159.3 s, 0 failures** |
| Course inventory | **18 modules, 105 lesson files, 26 notebooks, 52 labs/project briefs, 21 assessments** |
| Markdown links and anchors | **295 files, 0 broken** |
| Strict MkDocs build | **0 warnings, 322 built pages** |
| Built-site links and `/AITopics` prefix | **PASS** |
| Licensing | **PASS: 8 checks, 561 release files classified at that time** |
| Whitespace | **`git diff --check` and `git diff --cached --check` clean** |
| GitHub Pages | **HTTP 404; not deployed** |
| GitHub Actions validation/deploy | **No run found; 2 Dependabot runs only** |

The detailed evidence is in the [Repository content audit](repository-content-audit.md),
[Notebook coverage audit](notebook-coverage-audit.md),
[Navigation and link audit](navigation-and-link-audit.md),
[GitHub Pages deployment audit](github-pages-deployment-audit.md), and
[Student usability audit](student-usability-audit.md).

The previous audit failed because seven modules published plans and projects but
no lessons. That gap was closed in the preceding pass: **33 new lessons, five
section indexes, five assessments, eight lab briefs, and seven executed
notebooks** now cover M04-M08 and M15-M17.

## Module status

| Module | Teaching material | Notebook | Practical work | Verdict |
| --- | --- | --- | --- | --- |
| M00 orientation | Roadmap, learning paths, study guide, plan | n/a | Study plan exercise | Complete for its scope |
| M01 environment | F02 | Executed | Lab + assessment | Complete |
| M02 ML foundations | F03-F10 | 8 executed | 8 labs + assessments | Complete |
| M03 deep learning | F11-F13 | 3 executed | 3 labs + assessments | Complete |
| M04 training from scratch | MT01-MT05 | `m04_training_from_scratch` executed | 2 lab briefs + assessment | Complete |
| M05 dataset preparation | MT06-MT10 | `m05_data_engineering` executed | 2 lab briefs + assessment | Complete |
| M06 transformers | LF01-LF04 | `m06_transformers` executed | 3 shared lab briefs + assessment | Complete |
| M07 supervised fine-tuning | LF05-LF07 | `m07_sft_small_lm` executed | 3 shared lab briefs + assessment | Complete |
| M08 LoRA and quantization | LF08-LF10 | `m08_lora_qlora` executed | 3 shared lab briefs + assessment | Complete |
| M09 chatbots | CA01-CA08 | `m09_chatbots` executed | 8 projects + assessment | Complete |
| M10 RAG | CA09-CA16 | `m10_rag` executed | 8 projects + assessment | Complete |
| M11 image classification | CV01-CV10 | `m11_image_classification` executed | 8 labs + assessment | Complete |
| M12 detection and tracking | CV08-CV14 | `m12_object_detection` executed | Labs 4-8 | Complete |
| M13 speech and audio | SA01-SA14 | `m13_speech_audio` executed | 8 labs + assessment | Complete |
| M14 video AI | VD01-VD15 | `m14_video_ai` executed | 8 labs + assessment | Complete |
| M15 agents | AG01-AG05 | `m15_agents` executed | 1 lab brief + assessment | Complete |
| M16 production | PR01-PR05 | `m16_production` executed | 1 lab brief + assessment | Complete |
| M17 capstone | CP01-CP03 | Reuses M04-M16 | 1 gated lab + assessment | Complete; agent-simulated pilot only |

Current published totals: **105 unique advertised lesson files, 26 executable
notebooks, 52 unique lab/project briefs, 21 unique assessments, 12 capstone
specifications with weighted rubrics, and 8 assessment banks with answer keys**.

## What was authored

### M04-M05 - Model Training

`docs/lessons/model-training/`: `index.md`, `assessment.md`, ten lessons
(`mt01-training-loop.md` through `mt10-dataset-cards.md`), and two lab briefs
(`lab-1-training-ablation.md`, `lab-2-dataset-audit.md`).

Measured anchors from the executed notebooks:

* 300 synthetic images split 210/45/45; random split leaks 91 near-duplicates,
  grouped split leaks 0;
* random-split accuracy 0.867 versus grouped 0.622 (premium slice 0.244), the
  leakage demonstration;
* plain test accuracy 0.956 versus augmented 1.000;
* bf16 3.50 ms/step versus fp32 1.73 ms/step on this CPU, reported as a measured
  negative result;
* checkpoint restore is exact; error analysis finds 2 errors, both
  circle-to-triangle;
* dataset cleaning: 650 to 600 rows, 10 blank labels, 49 duplicates; vocabulary
  533; 24,976 near-duplicate pairs; noise curve 1.000/0.868/0.794/0.382;
  Cohen's kappa 0.866/0.723/0.509.

### M06-M08 - LLM Fine-Tuning

`docs/lessons/llm-fine-tuning/`: `index.md`, `assessment.md`, ten lessons
(`lf01-tokens-and-embeddings.md` through `lf10-merging-and-serving.md`), and three
lab briefs (`lab-1-tiny-lm.md`, `lab-2-sft-and-lora.md`,
`lab-3-efficiency-report.md`).

Measured anchors:

* M06: 239,040 parameters, 400 steps in 22.8 s CPU (24.8 s in an earlier run), loss 3.454 to 0.433,
  validation perplexity 1.54;
* M07: answer loss 1.039 to 0.315; exact match 0.688 to 0.905; first-12 tokens
  0.411 to 0.818; word F1 0.087 to 0.258; forgetting 0.885 to 1.072, reported;
* M08: LoRA 8,448 parameters (3.34%), answer loss 0.601 versus 0.315, accuracy
  0.816 versus 0.905; merge delta 6.7e-6; int8 259.8 KiB (3.758x), int4 139.1 KiB
  (7.022x), accuracy 0.905/0.900, agreement 0.992/0.895.

Shared code: `projects/llm-fine-tuning/llm_core/` (data, tokenizer, model, train,
SFT, LoRA, quantization, evaluation), covered by 33 tests.

### M15 - AI Agents

`docs/lessons/ai-agents/`: `index.md`, `assessment.md`, five lessons
(`ag01-agent-loop.md` through `ag05-injection-and-evaluation.md`), one lab brief.

Measured anchors: a two-tool task stops `final` after 3 steps and 2 calls; a
repeating model stops with `repeated_action`; an unapproved write returns
`approval_denied`; a path escape returns `policy_denied` even with approval; the
untrusted-output envelope is visible; the evaluation suite scores 2/3 because a
deliberate negative control fails.

A real defect was found and fixed: `projects/ai-agents/agent_core/memory.py`
compared trust with the wrong inequality, allowing a `tool`-trusted entry through a
`user` bar. `recall` and `search` now reject entries below the requested trust.
Regression tests: `tests/test_ai_agents_memory.py` (4 tests).

### M16 - Production

`docs/lessons/production/`: `index.md`, `assessment.md`, five lessons
(`pr01-metrics-and-intervals.md` through `pr05-artifacts-and-serving.md`), one lab
brief.

Measured anchors: AUC 0.778; accuracy 0.790 (293/371), Wilson [0.745, 0.828];
precision/recall/F1 0.658/0.475/0.552; MAE 0.329 [0.308, 0.350]; ECE 0.067 raw and
0.075 after temperature 1.10, a measured regression with a paired interval that
excludes zero; drift week 1 hold, week 2 investigate (usage PSI 1.171, tickets
1.212, region 0.492); guard recall 0.75 with false-positive rate 0.0 and four
documented misses; card audit passes; tampering detected; 40/40 HTTP 200, p50
15.53 ms, p95 16.72 ms (an earlier run measured p95 16.31 ms; loopback jitters).

### M17 - Capstone

`docs/lessons/capstone/`: `index.md`, `assessment.md`, three lessons
(`cp01-scoping-and-data.md`, `cp02-build-and-evidence.md`,
`cp03-evaluation-and-packaging.md`), one lab brief with three gated checkpoints
(20/35/45).

The capstone deliberately adds no notebook. It requires reusing the M04-M16
notebooks and packages in one project, which is the integration the module is for.

Measured anchors from the agent-simulated pilot (P03, P06, P12), recorded in the
[capstone pilot report](capstone-pilot-report.md):

* P03 CPU character model: masked token accuracy 0.302/0.413/0.325 for
  base/full/LoRA, but held-out free generation scored 0.134/0.110/0.153 word F1
  with zero exact matches and degenerate `the the the` output; 800 SFT steps raised
  token accuracy to 0.725 without fixing prose. A word-tokenizer control produced
  readable text (full SFT 0.977 token accuracy, 0.705 word F1) with wrong product
  slots, isolating the tokenizer/architecture limit;
* P06: `objects_p06` has 960 images from 240 sources, split 672/144/144 with 36
  test per class and zero source overlap. Scratch CNN 0.9792 accuracy, macro F1
  0.9791, bootstrap interval [0.9514, 1.0000]; temperature scaling cut ECE from
  0.0458 to 0.0214; brightness 0.6 fell to 0.5208 and TTA did not rescue it;
* P12: scripted 15/15 dev and 5/5 test, but the deterministic malformed-call mock
  also scored 15/15 with a 0.50 tool-error rate, and a cached 135M local model
  completed 0/5 tasks because it never emitted a valid JSON decision. The approval
  gate, path containment, schema validation and step budget held in every gated
  attack; the ungated ablation wrote the outbox and the post-denial note.

## Historical executed checks (2026-11-06 pass)

Environment: Windows 11, Python 3.12.10, CPU only. Commands were run from the
repository root on 2026-11-06 in the project virtual environment. The current
2026-11-09 results are in the table at the top of this page and in the
[Notebook coverage audit](notebook-coverage-audit.md).

| Check | Command | Result |
| --- | --- | --- |
| Full unit suite | `.venv/Scripts/python.exe -m unittest discover -s tests` | **233 tests, OK** (219 prior + 12 P06 manifest + 2 submission package) |
| LLM package tests | included in discovery | 37 pass |
| Agent memory regression | included in discovery | 4 pass |
| Agent security tests | `python -m unittest tests.test_ai_agents_security` | 6 pass |
| Course project structure | `python scripts/check_course_projects.py` | Pass: 12 projects, 12 complete specs, 8 assessment banks with solutions |
| Documentation links and anchors | `python scripts/check_docs_links.py` | Pass: **280 Markdown files**, all links, anchors, and nav entries resolve |
| Strict site build | `python -m mkdocs build --strict` | Pass: 0 warnings, 6.6 s |
| Built-site prefix check | `python scripts/check_docs_links.py --site site` | Pass: **279 built pages**, relative URLs resolve, absolute URLs carry `/AITopics` |
| Notebook JSON validity | `nbformat.validate` on all 20 | Pass |
| Notebook execution | `nbclient` restart-and-run-all on the 7 new notebooks | Pass: 0 error outputs, 0 unexecuted code cells |
| Lesson structure | 33 new lessons checked for objectives, prerequisites, study time, beginner-to-advanced sections, practice, mistakes, knowledge checks, lab link, further reading, prev/next | Pass: no missing block |
| Duplicate check | identical-content and duplicate-title scan over `docs/lessons/` | Pass: none |
| Python syntax | `compileall` over `scripts/`, `projects/`, `tests/`, `labs/` | Pass |
| Lab selftests | 49 scripts with `--selftest` | 49/49 pass, recorded before this pass |
| Agent project selftests | 8 `projects/ai-agents/project_*.py --selftest` | 8/8 pass after the memory fix |
| Capstone pilot | Three agent-simulated projects: P03, P06, P12 | Mechanics run, measurements recorded, and P03/P06/P12 defects fixed; see [Capstone pilot report](capstone-pilot-report.md). No human submission. |
| Capstone data checks | `scripts/make_capstone_data.py --check`, `scripts/make_agent_data.py --check`, `scripts/make_vision_data.py --check` | 9 capstone files, 12 agent files, and 960 P06 images verified; 0 problems, 57 duplicate-variant warnings |
| P06 manifest tamper tests | `python -m unittest tests.test_computer_vision.TestDatasetManifest` | 12/12 pass: missing, modified, unexpected, duplicate, cross-split, label conflict, missing class, overlap, count mismatch, determinism |
| P06 deduplication study | `python tmp/p06-dedup-study/run_study.py` | 57 duplicate groups / 58 extra files, all same source/label/split and byte-identical; the 902-image dedup and 240-image balanced manifests pass with 0 warnings; clean accuracy A 0.9931, B 0.9931, C 0.9861; no consistent robustness or calibration gain; v1.0.0 retained |
| Submission package | `python -m unittest tests.test_course_projects` | 6/6 pass; all ten template files present and documented |
| P06 CLI | `tmp/capstone-pilot/p06/predict.py` with the new checkpoint | Top-3 probabilities and `abstain: false` on the stored sample |

### Notebook execution detail

All seven new notebooks were executed top-to-bottom from a fresh kernel on
2026-11-06, each ending with its own validation cell:

| Notebook | Cells | Validation |
| --- | --- | --- |
| `m04_training_from_scratch.ipynb` | 20 | `M04 validation passed.` |
| `m05_data_engineering.ipynb` | 21 | `M05 validation passed.` |
| `m06_transformers.ipynb` | 23 | `M06 validation passed.` |
| `m07_sft_small_lm.ipynb` | 21 | `M07 validation passed.` |
| `m08_lora_qlora.ipynb` | 17 | `M08 validation passed.` |
| `m15_agents.ipynb` | 26 | `M15 validation passed.` |
| `m16_production.ipynb` | 24 | `M16 validation passed.` |

The thirteen foundation notebooks retain their earlier executed outputs and also
have 0 error outputs. All 26 notebooks contain no unexecuted code cell. The six
M09-M14 notebooks were added and executed on 2026-11-08; the current full run is
recorded in the [Notebook coverage audit](notebook-coverage-audit.md).

## Curriculum coverage

The module-to-lesson mapping is in
[Curriculum coverage](../planning/curriculum-coverage.md). It records, for every
module, the lesson files, notebook, labs, assessment, measured anchors, reused
packages, and known limitations.

No duplicate implementations were created to inflate file counts:

* `vision_core` is reused by M04/M05 data and metrics;
* `agent_core` is reused by M15;
* `eval_core` is reused by M16;
* one new package, `llm_core`, was necessary because no existing package covered
  tokenization, SFT masking, LoRA, or quantization;
* the capstone reuses `vision_core`; the P06 manifest/checker is part of that package,
  and the submission package is documentation and templates only.

## Remaining findings and risks

| Finding | Severity | Detail |
| --- | --- | --- |
| No GPU execution | Medium | All 26 notebooks ran on Windows 11 CPU. GPU paths are documented and labelled optional; no GPU number is claimed. |
| M07/M08 pretrained path not executed | Medium | The Hugging Face 4-bit QLoRA path needs a GPU and a download. The mandatory path is a CPU-sized local implementation; the pretrained path is optional and marked unexecuted. |
| No Colab verification | Medium | No Colab session was run for any notebook. |
| No human capstone pilot | Medium | An agent-simulated pilot ran P03, P06, and P12 through their pipelines and gates; no human student or human marker has done so. See [Capstone pilot report](capstone-pilot-report.md). |
| Capstone evidence is prototype-grade | Medium | P03's CPU model is a measured no-release on generation quality; P06's 960 images are synthetic from one renderer; P12's success numbers come from a scripted policy, and the local 135M model failed the decision protocol. The briefs and pilot report state each boundary. |
| P06 has 57 duplicate variants | Low | Two variants of the same source and label render identical bytes within a split. No duplicate crosses a split or a label, so this is redundancy, not leakage. A controlled deduplication study found no clean-accuracy, calibration, or robustness benefit from removing the copies; v1.0.0 stays recommended and `1.1.0-dedup` is optional. See the [P06 deduplication study](p06-deduplication-study.md). |
| Lab 3 (computer vision) transfer numbers do not reproduce | High | Pre-existing, unchanged: repeated runs give 0.667 or 0.500 for the fine-tuned condition against the recorded 0.500/0.500/0.722. Needs a documented seed, larger test set, or retuned rate, plus a content decision. |
| Video Lab 2 not executed | Medium | Pre-existing: it downloads a 13 MB checkpoint. |
| Licence implementation review | Low | The approved MIT, CC BY 4.0, and CC0 1.0 files and validator are present in the working tree; instructor review and commit remain. |
| GitHub Pages API 404, no deployment | Medium | Workflows validate; the repository setting and first run are manual. The Pages API and public URL returned HTTP 404 on 2026-11-09. No public URL is claimed. |
| CI does not yet cover code and notebooks on GitHub | Medium | The validation workflow installs the CPU stack, runs licensing validation and 269 tests, checks manifests and projects, and executes all 26 notebooks locally. The first GitHub Actions run is still pending; only two Dependabot runs are present. |
| `scikit-learn` DLL blocked in this environment | Low | M05 uses inline Naive Bayes and kappa; documented in the notebook and coverage map. |

## Responsible AI and security

The new sections continue the repository's rules: synthetic or CC0 data, no
account or paid API for mandatory work, dataset and model cards with licences,
explicit limitations, agent capability limits and approval gates, untrusted tool
output kept out of the instruction channel, guard recall reported with false
positives and misses, and model-card claims audited against measured metrics. No
credential-shaped string appears in tracked files, and the notebooks do not read
API keys.

## Manual publication commands

The full procedure, with the browser checks and failure table, is in
[GitHub Pages publication](GITHUB-PAGES.md#release-publication-procedure-nine-steps).
These are the exact commands for this candidate, run from the repository root
after reviewing the diff above:

```bash
# 1. Review (must show 0 staged, 59 tracked, 12 untracked before staging)
git status --porcelain=v1 -uall && git diff --stat && git diff --check

# 2. Commit the reviewed tree
git add -A && git diff --cached --stat
git commit -F - <<'MSG'
Repair course navigation and prepare GitHub Pages publication

Add the datasets/resources page, lab READMEs, module links, and notebook
Markdown repairs; widen validation and Pages deployment to release branches;
add inventory floors, JSON output, and parser regression tests.
MSG

# 3. Push only this branch
git push origin release/v0.1.0-rc.1

# 4. Confirm the remote commit is the reviewed commit
git fetch origin && git rev-parse HEAD origin/release/v0.1.0-rc.1
git rev-list --left-right --count origin/release/v0.1.0-rc.1...HEAD   # expect: 0  0

# 5. One-time setting: Settings -> Pages -> Source: GitHub Actions
gh api -X POST repos/nadeem-majeedch/AITopics/pages -f build_type=workflow
gh api repos/nadeem-majeedch/AITopics/pages --jq '.build_type'          # expect: workflow

# 6. Validation runs from the push; watch it
gh run list --workflow=validate-docs.yml --branch release/v0.1.0-rc.1 --limit 3
gh run watch <run-id> --exit-status

# 7. Deployment follows a successful validation
gh run list --workflow=deploy-pages.yml --limit 3
gh run watch <run-id> --exit-status
```

Do not tag, create a release, force-push, or change any other repository setting
as part of this publication.

## Deployment verification procedure

A successful run is not a published site. Verify in this order and record each
result in the [verification log](build-and-deploy.md#verification-log):

1. **Run level.** `gh run view <run-id> --json conclusion,headSha,url` reports
   `success`, and `headSha` equals the commit from step 4. The deploy job shows a
   `github-pages` environment URL.
2. **HTTP level.** These must return `200`:

   ```bash
   curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/
   curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/course/projects/
   curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/notebooks/production/m16_production/
   curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/sitemap.xml
   ```

3. **Content level.** The canonical link carries the `/AITopics/` prefix, the
   stylesheet loads, and `gh api repos/nadeem-majeedch/AITopics/pages --jq
   .status` no longer reports a missing site.
4. **Notebook download.** The M16 page's **Download notebook (.ipynb)** button
   must return the file. Compare its SHA-256 with
   `git show HEAD:notebooks/production/m16_production.ipynb`, not with the working
   tree: on Windows the checkout is CRLF and a working-tree comparison reports a
   false mismatch. No manifest is committed, so this hash comparison is the check.
5. **Clean browser.** In a private window with an empty cache, check styling,
   search, a deep project page, the M16 notebook page and its download, the
   site's own 404 page, the **Edit this page** link pointing at
   `release/v0.1.0-rc.1`, and the layout at about 390 px.

Until steps 1-5 are recorded, the Pages status in this audit stays
**not deployed**.

## Manual tasks remaining

1. Review and commit the licence implementation (`LICENSE`, `LICENSES/`,
   `licensing-scope.json`, validator, and notices) after instructor review. It is
   part of the 71-path candidate above.
2. Push the release branch (currently one commit ahead of the remote plus this
   uncommitted tree) and let **Validate repository** run on it, per the commands
   above.
3. Enable **Settings → Pages → Source: GitHub Actions**, run the deploy workflow,
   verify the URL with the procedure above, and record it in the verification log.
4. Run representative notebooks on Google Colab and, if hardware allows, on a GPU.
5. Run one **human** capstone pilot through the three checkpoints and mark it
   with the published rubric. The agent-simulated pilot is complete; it is not a
   substitute for a person.
6. Resolve the Lab 3 transfer comparison in a content review.
7. Run the new whole-repository validation workflow on GitHub Actions after
   merge; local execution and schema validation are complete, but no runner has
   executed it yet.
8. Repeat P06 on real photographs and P12 with a larger model using constrained
   JSON decoding, so the prototype results have a real-data and real-model
   counterpart.

## Files changed during the 2026-11-08 completion pass

### New lessons and section pages

* `docs/lessons/model-training/mt01-training-loop.md` through `mt10-dataset-cards.md`
* `docs/lessons/model-training/index.md`, `assessment.md`
* `docs/lessons/model-training/labs/lab-1-training-ablation.md`, `lab-2-dataset-audit.md`
* `docs/lessons/llm-fine-tuning/lf01-tokens-and-embeddings.md` through `lf10-merging-and-serving.md`
* `docs/lessons/llm-fine-tuning/index.md`, `assessment.md`
* `docs/lessons/llm-fine-tuning/labs/lab-1-tiny-lm.md`, `lab-2-sft-and-lora.md`, `lab-3-efficiency-report.md`
* `docs/lessons/ai-agents/ag01-agent-loop.md` through `ag05-injection-and-evaluation.md`
* `docs/lessons/ai-agents/index.md`, `assessment.md`, `labs/lab-1-support-agent.md`
* `docs/lessons/production/pr01-metrics-and-intervals.md` through `pr05-artifacts-and-serving.md`
* `docs/lessons/production/index.md`, `assessment.md`, `labs/lab-1-evaluation-and-serving.md`
* `docs/lessons/capstone/cp01-scoping-and-data.md`, `cp02-build-and-evidence.md`, `cp03-evaluation-and-packaging.md`
* `docs/lessons/capstone/index.md`, `assessment.md`, `labs/lab-1-capstone-package.md`
* `docs/planning/curriculum-coverage.md`

### New notebooks and code added on 2026-11-08

* `notebooks/chatbots-rag/m09_chatbots.ipynb`
* `notebooks/chatbots-rag/m10_rag.ipynb`
* `notebooks/computer-vision/m11_image_classification.ipynb`
* `notebooks/computer-vision/m12_object_detection.ipynb`
* `notebooks/speech-audio/m13_speech_audio.ipynb`
* `notebooks/video-ai/m14_video_ai.ipynb`
* `docs/notebook-library.md`
* `scripts/check_course_inventory.py`
* `projects/chatbots-rag/chatbot_core/model_client.py` (support-rule regression fix)
* `docs/technical/repository-content-audit.md`
* `docs/technical/notebook-coverage-audit.md`
* `docs/technical/navigation-and-link-audit.md`
* `docs/technical/github-pages-deployment-audit.md`
* `docs/technical/student-usability-audit.md`

### Earlier notebooks and code

* `notebooks/model-training/m04_training_from_scratch.ipynb`
* `notebooks/model-training/m05_data_engineering.ipynb`
* `notebooks/llm-fine-tuning/m06_transformers.ipynb`
* `notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb`
* `notebooks/llm-fine-tuning/m08_lora_qlora.ipynb`
* `notebooks/ai-agents/m15_agents.ipynb`
* `notebooks/production/m16_production.ipynb`
* `projects/llm-fine-tuning/llm_core/` (9 modules)
* `projects/ai-agents/agent_core/memory.py` (trust-ordering fix)
* `projects/ai-agents/agent_core/model.py` (local model chat template)
* `projects/llm-fine-tuning/llm_core/sft.py` (bounded prompt and answer)
* `projects/llm-fine-tuning/llm_core/evaluate.py` (`generation_report`, stop tokens)
* `projects/computer-vision/vision_core/datasets.py` (`stratified_group_split`)
* `projects/computer-vision/vision_core/manifest.py` (manifest build and integrity check)
* `tests/test_computer_vision.py` (12 manifest tests)
* `tests/test_course_projects.py` (2 submission-package tests)
* `tests/test_llm_fine_tuning.py` (37 tests)
* `tests/test_ai_agents_memory.py` (4 tests)
* `tests/test_ai_agents_security.py` (6 tests)
* `scripts/make_training_data.py` (uniqueness fix)
* `scripts/make_capstone_data.py` (product grounding, generation split)
* `scripts/make_vision_data.py` (`objects_p06`, manifest/`--check`, per-class split counts)
* `data/capstones/instructions/generation_eval.jsonl` (40 held-out prompts, generated)
* `data/computer-vision/objects_p06/` (960 images, 240 source groups, generated)
* `templates/capstone-submission/` (ten submission files plus `experiments.csv`)
* `docs/course/projects/submission-package.md` (structure, checkpoint map, checklist, failure-reporting rules)
* `docs/technical/p06-deduplication-study.md` (duplicate analysis, three datasets, controlled training, decision)
* `tmp/p06-dedup-study/run_study.py` and its local outputs (untracked experiment; original data untouched)

### Navigation and status

* `mkdocs.yml` (five section nav trees and the coverage page)
* `docs/lessons/index.md`
* `docs/index.md`
* `docs/syllabus/index.md`
* `docs/syllabus/level-1-foundations.md`
* `docs/syllabus/level-2-language.md`
* `docs/syllabus/level-3-vision-video.md`
* `docs/syllabus/level-4-agents.md`
* `docs/syllabus/level-5-production.md`
* `docs/planning/content-inventory.md`
* `docs/planning/implementation-phases.md`
* `README.md`
* `docs/technical/final-audit.md` (this page)
* `docs/technical/capstone-pilot-report.md` (agent-simulated pilot)
* `docs/course/projects/p03-lora-finetune.md`, `p06-image-classifier.md`,
  `p12-tool-using-agent.md`, `index.md` (capstone usability fixes)
* `docs/lessons/capstone/labs/lab-1-capstone-package.md` (classification gate)

No previously validated computer-vision, speech, or video experiment was modified.
No course chapter was deleted. Nothing was committed or pushed.

## Files changed during the 2026-11-09 repair pass

### Created

* `docs/resources/index.md`
* `docs/technical/repository-inventory.json`
* `labs/README.md`
* `labs/ai-agents/README.md`, `labs/chatbots-rag/README.md`,
  `labs/computer-vision/README.md`, `labs/llm-fine-tuning/README.md`,
  `labs/model-training/README.md`, `labs/production/README.md`,
  `labs/speech-audio/README.md`, `labs/video-ai/README.md`

### Changed

* Navigation and syllabus: `docs/course/roadmap.md`,
  `docs/course/learning-paths.md`, `docs/syllabus/index.md`,
  `docs/syllabus/level-0-start.md` through `docs/syllabus/level-5-production.md`,
  `docs/course/assessments/index.md`, `docs/planning/curriculum-coverage.md`,
  `docs/planning/content-inventory.md`, `docs/planning/repository-architecture.md`,
  `docs/index.md`, `docs/about/instructor.md`, `README.md`, `mkdocs.yml`,
  `docs/technical/GITHUB-PAGES.md`, `docs/technical/build-and-deploy.md`,
  `docs/technical/contributing.md`.
* Notebook rendering: `notebooks/model-training/m04_training_from_scratch.ipynb`,
  `m05_data_engineering.ipynb`, `notebooks/llm-fine-tuning/m06_transformers.ipynb`,
  `m07_sft_small_lm.ipynb`, `m08_lora_qlora.ipynb`,
  `notebooks/ai-agents/m15_agents.ipynb`, `notebooks/production/m16_production.ipynb`.
* Video data instructions and code: `docs/lessons/video-ai/governance.md`,
  `index.md`, `model-card.md`, `vd15-responsible-video-analytics.md`,
  `labs/lab-1-preprocessing.md`, `projects/video-ai/lab_support.py`,
  `requirements/video.txt`.
* Publication and accounting: `.github/workflows/deploy-pages.yml`,
  `.github/workflows/validate-docs.yml`, `scripts/check_course_inventory.py`,
  `docs/technical/repository-content-audit.md`,
  `docs/technical/notebook-coverage-audit.md`,
  `docs/technical/navigation-and-link-audit.md`,
  `docs/technical/github-pages-deployment-audit.md`,
  `docs/technical/student-usability-audit.md`, `docs/technical/final-audit.md`,
  `docs/technical/release-notes-v0.1.0-rc.1.md`,
  `docs/technical/release-readiness-audit.md`,
  `docs/technical/v1-release-candidate-checklist.md`,
  `docs/technical/licensing-decision-package.md`.

### Deleted

* `labs/ai-agents/.gitkeep`, `labs/chatbots-rag/.gitkeep`,
  `labs/computer-vision/.gitkeep`, `labs/foundations/.gitkeep`,
  `labs/llm-fine-tuning/.gitkeep`, `labs/model-training/.gitkeep`,
  `labs/production/.gitkeep`, `labs/speech-audio/.gitkeep`,
  `labs/video-ai/.gitkeep`. These were empty placeholders; the directories now
  contain substantive README pointers or real foundation starter files.

### Preserved without reverting

These pre-existing working-tree changes were present before this pass and were
not reverted, overwritten, or included in a commit:

* `docs/lessons/chatbots-rag/ca14-evaluation.md`
* `docs/lessons/chatbots-rag/index.md`
* `docs/technical/licensing-decision-package.md` (its link/site counts were
  updated to 296/323; it was not otherwise rewritten)
* `projects/chatbots-rag/chatbot_core/model_client.py`
* `tests/test_chatbot_parser_regression.py` (untracked)

All changes in this pass are unstaged. No commit, push, tag, release, or remote
setting change was made.

## Related documents

- [Capstone pilot report](capstone-pilot-report.md)
- [Curriculum coverage](../planning/curriculum-coverage.md)
- [GitHub Pages publication](GITHUB-PAGES.md)
- [Build and deploy](build-and-deploy.md)
- [Site maintenance](site-maintenance.md)
- [Quality standards](../planning/quality-standards.md)
