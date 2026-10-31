# Content inventory

This inventory records what existed before the architecture work, what must be
preserved, and what remains to be created. It is a working checklist for
maintainers.

## Audit result

| Item | Result |
| --- | --- |
| Local files in `E:\AITopics` | None at audit time |
| Git repository | Not initialized locally |
| Remote repository | `https://github.com/nadeem-majeedch/AITopics` returned HTTP 404 |
| GitHub account | Public account exists; repository not publicly accessible |
| GitHub Pages | Not found |
| Documentation framework | Not found |
| Notebooks | None |
| Tests | None |
| CI workflows | None |
| License | None |
| Completed work to preserve | None accessible |

The workspace was empty. No existing file was overwritten or deleted.

## Files to preserve

**Current status:** none found.

If a private or renamed repository exists, preserve these categories before
making changes:

| Category | Preserve because | Action |
| --- | --- | --- |
| Student README | It may contain course identity, contact, or policies | Merge, do not replace |
| Existing notebooks | They may contain completed labs or solutions | Copy to a quarantine branch; compare before reuse |
| Dataset cards and scripts | Licenses and provenance may be hard to recover | Keep and reconcile |
| GitHub workflows | Deployment may already exist | Inspect before changing; do not replace blindly |
| License files | Legal terms cannot be changed casually | Keep exact text; ask the instructor |
| Images and diagrams | Provenance and alt text may be lost | Keep with attribution |
| Branch protection and Pages settings | Changing them can break the live site | Do not modify during reconciliation |
| Student contributions | They may be in open pull requests | Review and preserve authorship |

### Reconciliation if a remote repository exists

1. Clone the remote into a separate directory; do not clone over this workspace.
2. Record `git log`, branches, tags, and open pull requests.
3. Compare the remote tree with this architecture.
4. Map existing content into the target structure without overwriting:
   - Lessons to `docs/lessons/`.
   - Notebooks to `notebooks/<area>/`.
   - Labs to `labs/<area>/`.
   - Dataset material to `datasets/` (cards and scripts only).
5. Preserve git history. Use merges or cherry-picks, not a fresh initial commit.
6. Keep any existing license unchanged until the instructor approves a change.
7. Re-run the content inventory and update this page.
8. When in doubt, move content aside or duplicate it; do not delete.

## Missing resources checklist

Status values: **Available**, **Partial**, **Planned**, **Blocked**.

### Governance and repository

| Resource | Path | Phase | Status |
| --- | --- | --- | --- |
| Student README | `README.md` | 0 | Available |
| MkDocs config | `mkdocs.yml` | 0 | Available |
| Git ignore rules | `.gitignore` | 0 | Available |
| Documentation requirements | `requirements/docs.txt` | 0 | Available |
| Dependency matrix | `requirements/README.md` | 0 | Available |
| Editor config | `.editorconfig` | 1 | Planned |
| Pre-commit hooks | `.pre-commit-config.yaml` | 1 | Planned |
| Python package config | `pyproject.toml` | 1 | Planned |
| Shared package | `src/aitopics_course/` | 1 | Planned |
| Unit tests | `tests/` | 1 | Planned |
| Root contribution pointer | `CONTRIBUTING.md` | 1 | Planned |
| Code of conduct | `CODE_OF_CONDUCT.md` | 1 | Planned |
| Security policy | `SECURITY.md` | 1 | Planned |
| License texts | `LICENSE`, `LICENSES/` | 1 | Blocked |
| Issue templates | `.github/ISSUE_TEMPLATE/` | 1 | Planned |
| Pull request template | `.github/pull_request_template.md` | 1 | Planned |
| Docs workflow | `.github/workflows/docs.yml` | 1 | Planned |
| Lint and test workflow | `.github/workflows/ci.yml` | 1 | Planned |
| Notebook smoke workflow | `.github/workflows/notebook-smoke.yml` | 7 | Planned |
| Pages workflow | `.github/workflows/pages.yml` | 9 | Planned |

### Student-facing documentation

| Resource | Path | Phase | Status |
| --- | --- | --- | --- |
| Course home | `docs/index.md` | 0 | Available |
| Roadmap | `docs/course/roadmap.md` | 0 | Available |
| Learning paths | `docs/course/learning-paths.md` | 0 | Available |
| Study guide | `docs/course/how-to-study.md` | 0 | Available |
| Course conventions | `docs/course/course-conventions.md` | 1 | Available |
| Assessment guide | `docs/course/assessments.md` | 0 | Available |
| Capstone guide | `docs/course/projects.md` | 0 | Available |
| FAQ | `docs/course/faq.md` | 0 | Available |
| Instructor page | `docs/about/instructor.md` | 0 | Available |
| Lessons index | `docs/lessons/index.md` | 1 | Available |
| Foundation lessons F01-F13 | `docs/lessons/f01-python-ai/` through `docs/lessons/f13-reproducibility/` | 2 | Available: 52 pages |
| Foundation data and dependencies | `docs/technical/foundation-assets.md` | 2 | Available |
| Contributor templates | `docs/technical/templates/` | 1 | Available |
| Syllabus overview | `docs/syllabus/index.md` | 0 | Available |
| Level 0 plans | `docs/syllabus/level-0-start.md` | 0 | Available |
| Level 1 plans | `docs/syllabus/level-1-foundations.md` | 0 | Available |
| Level 2 plans | `docs/syllabus/level-2-language.md` | 0 | Available |
| Level 3 plans | `docs/syllabus/level-3-vision-video.md` | 0 | Available |
| Level 4 plan | `docs/syllabus/level-4-agents.md` | 0 | Available |
| Level 5 plans | `docs/syllabus/level-5-production.md` | 0 | Available |
| Resource catalog | `docs/resources/index.md` | 2 | Planned |
| Dataset catalog | `docs/resources/datasets.md` | 2 | Planned |
| Model catalog | `docs/resources/models.md` | 3 | Planned |
| Free compute guide | `docs/resources/free-compute.md` | 2 | Planned |
| Tool catalog | `docs/resources/tools.md` | 2 | Planned |
| Glossary | `docs/resources/glossary.md` | 7 | Planned |
| Errata | `docs/course/errata.md` | 7 | Planned |

### Lessons

Each lesson lives at `docs/lessons/<folder>/index.md`. A lesson is created only
when it can be completed to the quality standard; empty placeholder chapters are
not created.

| Module | Lesson folder | Phase | Status |
| --- | --- | --- | --- |
| M00 | `m00-orientation` | 2 | Planned |
| F01 | `f01-python-ai` | 2 | Available |
| F02 (M01) | `m01-environment` | 1 | Available |
| F03 | `f03-numpy-pandas` | 2 | Available |
| F04 | `f04-data-cleaning` | 2 | Available |
| F05 | `f05-splits` | 2 | Available |
| F06 | `f06-eda` | 2 | Available |
| F07 | `f07-supervised-unsupervised` | 2 | Available |
| F08 | `f08-regression-classification` | 2 | Available |
| F09 | `f09-tree-ensembles` | 2 | Available |
| F10 | `f10-metrics-validation` | 2 | Available |
| F11 | `f11-neural-networks` | 2 | Available |
| F12 | `f12-backpropagation` | 2 | Available |
| F13 | `f13-reproducibility` | 2 | Available |
| M02 | Delivered by F03-F10 | 2 | Available |
| M03 | Delivered by F11-F13 | 2 | Available |
| M04 | `m04-training-from-scratch` | 2 | Planned |
| M05 | `m05-data-engineering` | 2 | Planned |
| M06 | `m06-transformers` | 3 | Planned |
| M07 | `m07-fine-tuning` | 3 | Planned |
| M08 | `m08-lora-qlora` | 3 | Planned |
| M09 | `m09-chatbots` | 3 | Planned |
| M10 | `m10-rag` | 3 | Planned |
| M11 | `m11-image-classification` | 4 | Planned |
| M12 | `m12-detection-tracking` | 4 | Planned |
| M13 | `m13-speech-audio` | 4 | Planned |
| M14 | `m14-video-analytics` | 4 | Planned |
| M15 | `m15-agents` | 5 | Planned |
| M16 | `m16-production` | 6 | Planned |
| M17 | `m17-capstone` | 6 | Planned |

### Notebooks

| Module | Notebook | Phase | Status |
| --- | --- | --- | --- |
| F01 | `notebooks/foundations/f01_python_ai.ipynb` | 2 | Available on Windows CPU |
| F02 (M01) | `notebooks/foundations/m01_environment_check.ipynb` | 1 | Available on Windows; Colab pending |
| F03 | `notebooks/foundations/f03_numpy_pandas.ipynb` | 2 | Available on Windows CPU |
| F04 | `notebooks/foundations/f04_data_cleaning.ipynb` | 2 | Available on Windows CPU |
| F05 | `notebooks/foundations/f05_splits.ipynb` | 2 | Available on Windows CPU |
| F06 | `notebooks/foundations/f06_eda.ipynb` | 2 | Available on Windows CPU |
| F07 | `notebooks/foundations/f07_supervised_unsupervised.ipynb` | 2 | Available on Windows CPU |
| F08 | `notebooks/foundations/f08_regression_classification.ipynb` | 2 | Available on Windows CPU |
| F09 | `notebooks/foundations/f09_tree_ensembles.ipynb` | 2 | Available on Windows CPU |
| F10 | `notebooks/foundations/f10_metrics_validation.ipynb` | 2 | Available on Windows CPU |
| F11 | `notebooks/foundations/f11_neural_networks.ipynb` | 2 | Available on Windows CPU |
| F12 | `notebooks/foundations/f12_backpropagation.ipynb` | 2 | Available on Windows CPU |
| F13 | `notebooks/foundations/f13_reproducibility.ipynb` | 2 | Available on Windows CPU |
| M04 | `notebooks/model-training/m04_training_from_scratch.ipynb` | 2 | Planned |
| M05 | `notebooks/model-training/m05_data_engineering.ipynb` | 2 | Planned |
| M06 | `notebooks/llm-fine-tuning/m06_transformers.ipynb` | 3 | Planned |
| M07 | `notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb` | 3 | Planned |
| M08 | `notebooks/llm-fine-tuning/m08_lora_qlora.ipynb` | 3 | Planned |
| M09 | `notebooks/chatbots-rag/m09_chatbot.ipynb` | 3 | Planned |
| M10 | `notebooks/chatbots-rag/m10_rag.ipynb` | 3 | Planned |
| M11 | `notebooks/computer-vision/m11_image_classification.ipynb` | 4 | Planned |
| M12 | `notebooks/computer-vision/m12_detection_tracking.ipynb` | 4 | Planned |
| M13 | `notebooks/speech-audio/m13_speech_audio.ipynb` | 4 | Planned |
| M14 | `notebooks/video-ai/m14_video_analytics.ipynb` | 4 | Planned |
| M15 | `notebooks/ai-agents/m15_agents.ipynb` | 5 | Planned |
| M16 | `notebooks/production/m16_production.ipynb` | 6 | Planned |

M00 is a planning worksheet, and M17 is a capstone; neither has a guided
notebook.

### Labs and projects

| Module | Lab brief | Phase | Status |
| --- | --- | --- | --- |
| M00 | `labs/foundations/m00_study_plan.md` | 2 | Planned |
| F01 | `docs/lessons/f01-python-ai/lab.md` | 2 | Available |
| F02 (M01) | `docs/lessons/m01-environment/lab.md` | 1 | Available |
| F03 | `docs/lessons/f03-numpy-pandas/lab.md` | 2 | Available |
| F04 | `docs/lessons/f04-data-cleaning/lab.md` | 2 | Available |
| F05 | `docs/lessons/f05-splits/lab.md` | 2 | Available |
| F06 | `docs/lessons/f06-eda/lab.md` | 2 | Available |
| F07 | `docs/lessons/f07-supervised-unsupervised/lab.md` | 2 | Available |
| F08 | `docs/lessons/f08-regression-classification/lab.md` | 2 | Available |
| F09 | `docs/lessons/f09-tree-ensembles/lab.md` | 2 | Available |
| F10 | `docs/lessons/f10-metrics-validation/lab.md` | 2 | Available |
| F11 | `docs/lessons/f11-neural-networks/lab.md` | 2 | Available |
| F12 | `docs/lessons/f12-backpropagation/lab.md` | 2 | Available |
| F13 | `docs/lessons/f13-reproducibility/lab.md` | 2 | Available |
| M04 | `labs/model-training/m04_cnn_budget.md` | 2 | Planned |
| M05 | `labs/model-training/m05_dataset_card.md` | 2 | Planned |
| M06 | `labs/llm-fine-tuning/m06_tiny_lm.md` | 3 | Planned |
| M07 | `labs/llm-fine-tuning/m07_domain_sft.md` | 3 | Planned |
| M08 | `labs/llm-fine-tuning/m08_quantization_tradeoffs.md` | 3 | Planned |
| M09 | `labs/chatbots-rag/m09_chatbot_guardrails.md` | 3 | Planned |
| M10 | `labs/chatbots-rag/m10_rag_benchmark.md` | 3 | Planned |
| M11 | `labs/computer-vision/m11_domain_classifier.md` | 4 | Planned |
| M12 | `labs/computer-vision/m12_detect_track.md` | 4 | Planned |
| M13 | `labs/speech-audio/m13_asr_audio.md` | 4 | Planned |
| M14 | `labs/video-ai/m14_video_privacy.md` | 4 | Planned |
| M15 | `labs/ai-agents/m15_agent_eval.md` | 5 | Planned |
| M16 | `labs/production/m16_deploy_review.md` | 6 | Planned |

| Resource | Path | Phase | Status |
| --- | --- | --- | --- |
| M01 lab submission template | `labs/foundations/m01_environment_report.md` | 1 | Available |
| F01 lab starter | `labs/foundations/f01_python_toolkit.md` | 2 | Available |
| F03 lab starter | `labs/foundations/f03_data_audit.md` | 2 | Available |
| F04 lab starter | `labs/foundations/f04_student_cleaning.md` | 2 | Available |
| F05 lab starter | `labs/foundations/f05_leakage_audit.md` | 2 | Available |
| F06 lab starter | `labs/foundations/f06_house_eda.md` | 2 | Available |
| F07 lab starter | `labs/foundations/f07_customer_segments.md` | 2 | Available |
| F08 lab starter | `labs/foundations/f08_house_prices.md` | 2 | Available |
| F09 lab starter | `labs/foundations/f09_classifier_comparison.md` | 2 | Available |
| F10 lab starter | `labs/foundations/f10_overfitting_lab.md` | 2 | Available |
| F11 lab starter | `labs/foundations/f11_xor_mlp.md` | 2 | Available |
| F12 lab starter | `labs/foundations/f12_training_curves.md` | 2 | Available |
| F13 lab starter | `labs/foundations/f13_cpu_gpu_reproducibility.md` | 2 | Available |

| Resource | Path | Phase | Status |
| --- | --- | --- | --- |
| Capstone template | `projects/_template/` | 6 | Planned |
| Capstone README | `projects/README.md` | 6 | Planned |
| Proposal template | `projects/_template/proposal.md` | 6 | Planned |
| Report template | `projects/_template/reports/final-report.md` | 6 | Planned |
| Model card template | `projects/_template/reports/model-card.md` | 6 | Planned |
| Dataset card template | `projects/_template/data/dataset-card.md` | 6 | Planned |
| Security review template | `projects/_template/reports/security-review.md` | 6 | Planned |

### Dataset cards

| Dataset | Path | Phase | Status |
| --- | --- | --- | --- |
| Foundation synthetic tables (CC0) | `datasets/foundations/README.md` | 2 | Available |
| Course-owned documentation corpus | `datasets/aitopics-docs/` | 3 | Planned |
| TinyShakespeare | `datasets/tinyshakespeare/` | 3 | Planned |
| Fashion-MNIST | `datasets/fashion-mnist/` | 2 | Planned |
| CIFAR-10 | `datasets/cifar-10/` | 2 | Planned |
| California Housing | `datasets/california-housing/` | 2 | Planned |
| Oxford-IIIT Pet or alternative | `datasets/image-classification/` | 4 | Planned |
| Detection subset | `datasets/detection-subset/` | 4 | Planned |
| Speech Commands | `datasets/speech-commands/` | 4 | Planned |
| LibriSpeech or Common Voice | `datasets/asr/` | 4 | Planned |
| UCF101 subset | `datasets/ucf101/` | 4 | Planned |
| Licensed traffic clip | `datasets/traffic-clip/` | 4 | Planned |

Each folder will contain a card, a download script, and checksums. No raw data
will be committed.

### Automation and tests

| Resource | Path | Phase | Status |
| --- | --- | --- | --- |
| Link checker | `scripts/check_links.py` | 7 | Planned |
| Notebook runner | `scripts/run_notebook.py` | 1 | Planned |
| Notebook smoke runner | `scripts/smoke_notebooks.py` | 7 | Planned |
| Module scaffolder | `scripts/new_module.py` | 2 | Planned |
| Dataset downloader entry point | `scripts/download_data.py` | 2 | Planned |
| Package tests | `tests/test_*.py` | 1 | Planned |
| Dataset card schema test | `tests/test_dataset_cards.py` | 2 | Planned |
| Notebook smoke tests | `tests/notebooks/` | 7 | Planned |
| Base requirements | `requirements/base.txt` | 1 | Available |
| Notebook requirements | `requirements/notebooks.txt` | 1 | Available |
| CPU requirements | `requirements/cpu.txt` | 1 | Available |
| GPU requirements | `requirements/gpu.txt` | 1 | Available |
| LLM requirements | `requirements/llm.txt` | 3 | Planned |
| Agent requirements | `requirements/agents.txt` | 5 | Planned |
| Dev requirements | `requirements/dev.txt` | 1 | Planned |

### Assessment materials

| Resource | Path | Phase | Status |
| --- | --- | --- | --- |
| Standard lab rubric | `docs/course/assessments.md` | 0 | Available |
| Capstone rubric | `docs/course/assessments.md` | 0 | Available |
| Knowledge checks | Per module | 7 | Planned |
| Answer keys | Maintainer-only | 7 | Planned |
| Sample submissions | Maintainer-only | 7 | Planned |
| Reflection template | `labs/_templates/reflection.md` | 1 | Planned |
| Lab report template | `labs/_templates/report.md` | 1 | Planned |

## Module coverage matrix

Legend: **P** = plan published, **A** = available, **-** = not created.

| Module | Plan | Lesson | Notebook | Lab | Dataset card | Knowledge check | Solution (private) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M00 | P | - | n/a | - | n/a | - | - |
| M01 | P | A | A | A | n/a | A | - |
| M02 | P | A | A | A | A | A | - |
| M03 | P | A | A | A | A | A | - |
| M04 | P | - | - | - | - | - | - |
| M05 | P | - | - | - | - | - | - |
| M06 | P | - | - | - | - | - | - |
| M07 | P | - | - | - | - | - | - |
| M08 | P | - | - | - | - | - | - |
| M09 | P | - | - | - | - | - | - |
| M10 | P | - | - | - | - | - | - |
| M11 | P | - | - | - | - | - | - |
| M12 | P | - | - | - | - | - | - |
| M13 | P | - | - | - | - | - | - |
| M14 | P | - | - | - | - | - | - |
| M15 | P | - | - | - | - | - | - |
| M16 | P | - | - | - | - | - | - |
| M17 | P | - | n/a | template | - | - | - |

M02 and M03 are delivered by the F03-F10 and F11-F13 foundation units. Their
rows count those units, including one assessment per unit and a shared synthetic
dataset card.

## Release blockers

| Blocker | Why it matters | Resolution |
| --- | --- | --- |
| License not approved | Public reuse is legally undefined | Instructor decision; add `LICENSE` and `LICENSES/` |
| Remote repository inaccessible | Work may diverge from existing content | Reconcile before Phase 1 |
| Only M01-M03 are published | M04-M17 are still plans, so the course is not a complete learning resource | Continue Phases 2-6 |
| Foundation notebooks executed only on Windows 11 CPU | Cross-environment and GPU reproducibility are unverified | Execute representative units on Colab and, where available, a GPU; record the comparison |
| No CI | Regressions go unnoticed | Add docs, lint, and unit-test workflows |
| No pilot | Time estimates and labs are untested | Run Phase 8 |
| GitHub Pages disabled | No public site | Enable after license and QA gates |
| Dataset licenses unverified | Legal risk | Verify each dataset card |
| Privacy review pending for video/audio | Potential harm | Complete in Phase 4 |

## Verification commands

From the repository root:

```bash
# Confirm the working tree state (after git is initialized)
git status --short

# List tracked course files and check for accidental data
find . -path ./.git -prune -o -type f -print | sort

# Build the docs site strictly
python -m mkdocs build --strict

# Validate notebook JSON without executing
python -c "import nbformat,pathlib; [nbformat.validate(nbformat.read(p,as_version=4)) for p in pathlib.Path('notebooks/foundations').glob('*.ipynb')]; print('notebook JSON valid')"

# Execute the M01 notebook from a clean kernel
python -m jupyter nbconvert --to notebook --execute --inplace \
  notebooks/foundations/m01_environment_check.ipynb

# Check for large files before committing
find . -path ./.git -prune -o -type f -size +5M -print
```

Do not commit or push unless the instructor asks for it.

## Next actions

1. Execute representative foundation notebooks on Google Colab and record the comparison.
2. Ask a second person to complete an F01-F13 lab from the published brief.
3. Reconcile the remote repository if it exists.
4. Obtain the license decision.
5. Continue Phase 2 with M04-M05 content.
6. Update this inventory as each artifact moves from Planned to Available.
