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
| License | None at the initial audit; implemented and verified 2026-11-07 |
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
| Unit tests | `tests/` | 1 | Available |
| Root contribution pointer | `CONTRIBUTING.md` | 1 | Planned |
| Code of conduct | `CODE_OF_CONDUCT.md` | 1 | Planned |
| Security policy | `SECURITY.md` | 1 | Planned |
| License texts | `LICENSE`, `LICENSES/` | 1 | Available (implemented 2026-11-07) |
| Issue templates | `.github/ISSUE_TEMPLATE/` | 1 | Planned |
| Pull request template | `.github/pull_request_template.md` | 1 | Planned |
| Docs validation workflow | `.github/workflows/validate-docs.yml` | 1 | Available (pull requests) |
| Lint and test workflow | `.github/workflows/ci.yml` | 1 | Planned |
| Notebook smoke workflow | `.github/workflows/notebook-smoke.yml` | 7 | Planned |
| Pages deployment workflow | `.github/workflows/deploy-pages.yml` | 1 | Available (push to `main`, manual dispatch) |

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
| Section lessons M04-M08, M15-M17 | `docs/lessons/model-training/`, `llm-fine-tuning/`, `ai-agents/`, `production/`, `capstone/` | 3-6 | Available: 51 pages |
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

Each section lives at `docs/lessons/<folder>/index.md`. A lesson is created only
when it can be completed to the quality standard; empty placeholder chapters are
not created.

| Module | Lesson folder | Pages | Status |
| --- | --- | --- | --- |
| M00 | Delivered by roadmap, learning paths, and study guide | n/a | Available |
| F01 | `f01-python-ai` | 4 | Available |
| F02 (M01) | `m01-environment` | 4 | Available |
| F03-F10 (M02) | `f03-numpy-pandas` through `f10-metrics-validation` | 32 | Available |
| F11-F13 (M03) | `f11-neural-networks` through `f13-reproducibility` | 12 | Available |
| M04-M05 | `model-training` | 10 lessons, index, assessment, 2 labs | Available |
| M06-M08 | `llm-fine-tuning` | 10 lessons, index, assessment, 3 labs | Available |
| M09-M10 | `chatbots-rag` | 16 modules, index, assessment, 8 projects | Available |
| M11-M12 | `computer-vision` | 14 modules, index, assessment, 8 labs | Available |
| M13 | `speech-audio` | 14 modules, index, assessment, 8 labs | Available |
| M14 | `video-ai` | 15 modules, index, assessment, 8 labs | Available |
| M15 | `ai-agents` | 5 lessons, index, assessment, 1 lab | Available |
| M16 | `production` | 5 lessons, index, assessment, 1 lab | Available |
| M17 | `capstone` | 3 lessons, index, assessment, 1 lab | Available |

### Notebooks

| Module | Notebook | Status |
| --- | --- | --- |
| F01 | `notebooks/foundations/f01_python_ai.ipynb` | Executed on Windows CPU |
| F02 (M01) | `notebooks/foundations/m01_environment_check.ipynb` | Executed on Windows CPU; Colab pending |
| F03-F10 | `notebooks/foundations/f03_numpy_pandas.ipynb` through `f10_metrics_validation.ipynb` | Executed on Windows CPU |
| F11-F13 | `notebooks/foundations/f11_neural_networks.ipynb` through `f13_reproducibility.ipynb` | Executed on Windows CPU |
| M04 | `notebooks/model-training/m04_training_from_scratch.ipynb` | Executed on Windows CPU |
| M05 | `notebooks/model-training/m05_data_engineering.ipynb` | Executed on Windows CPU |
| M06 | `notebooks/llm-fine-tuning/m06_transformers.ipynb` | Executed on Windows CPU |
| M07 | `notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb` | Executed on Windows CPU |
| M08 | `notebooks/llm-fine-tuning/m08_lora_qlora.ipynb` | Executed on Windows CPU |
| M09-M14 | Section projects are script-based | No notebook; runnable labs |
| M15 | `notebooks/ai-agents/m15_agents.ipynb` | Executed on Windows CPU |
| M16 | `notebooks/production/m16_production.ipynb` | Executed on Windows CPU |
| M17 | Reuses the M04-M16 notebooks and packages | Capstone is project work |

### Labs and projects

| Module | Lab brief | Status |
| --- | --- | --- |
| F01-F13 | `docs/lessons/f01-python-ai/lab.md` through `f13-reproducibility/lab.md` | Available |
| M04 | `docs/lessons/model-training/labs/lab-1-training-ablation.md` | Available |
| M05 | `docs/lessons/model-training/labs/lab-2-dataset-audit.md` | Available |
| M06 | `docs/lessons/llm-fine-tuning/labs/lab-1-tiny-lm.md` | Available |
| M07 | `docs/lessons/llm-fine-tuning/labs/lab-2-sft-and-lora.md` | Available |
| M08 | `docs/lessons/llm-fine-tuning/labs/lab-3-efficiency-report.md` | Available |
| M09-M10 | `docs/lessons/chatbots-rag/` project briefs | Available |
| M11-M12 | `docs/lessons/computer-vision/labs/` | Available |
| M13 | `docs/lessons/speech-audio/labs/` | Available |
| M14 | `docs/lessons/video-ai/labs/` | Available |
| M15 | `docs/lessons/ai-agents/labs/lab-1-support-agent.md` | Available |
| M16 | `docs/lessons/production/labs/lab-1-evaluation-and-serving.md` | Available |
| M17 | `docs/lessons/capstone/labs/lab-1-capstone-package.md` | Available |

| Resource | Path | Status |
| --- | --- | --- |
| M01 lab submission template | `labs/foundations/m01_environment_report.md` | Available |
| F01-F13 lab starters | `labs/foundations/` | Available |
| Shared LLM package | `projects/llm-fine-tuning/llm_core/` | Available |
| Shared vision package | `projects/computer-vision/vision_core/` | Available |
| Shared agent package | `projects/ai-agents/agent_core/` | Available |
| Shared evaluation package | `projects/production/eval_core/` | Available |
| Capstone templates | `docs/course/projects/` | Available |

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
| Link checker | `scripts/check_docs_links.py` | 7 | Available |
| Notebook runner | `scripts/run_notebook.py` | 1 | Planned |
| Notebook smoke runner | `scripts/smoke_notebooks.py` | 7 | Planned |
| Module scaffolder | `scripts/new_module.py` | 2 | Planned |
| Dataset downloader entry point | `scripts/download_data.py` | 2 | Planned |
| Package tests | `tests/test_*.py` | 1 | Available |
| Dataset card schema test | `tests/test_dataset_cards.py` | 2 | Planned |
| Notebook smoke tests | `tests/notebooks/` | 7 | Planned |
| Base requirements | `requirements/base.txt` | 1 | Available |
| Notebook requirements | `requirements/notebooks.txt` | 1 | Available |
| CPU requirements | `requirements/cpu.txt` | 1 | Available |
| GPU requirements | `requirements/gpu.txt` | 1 | Available |
| LLM requirements | `requirements/llm.txt` | 3 | Available |
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

Legend: **A** = available and executed, **n/a** = not applicable to the module.

| Module | Lesson | Notebook | Lab | Dataset card | Knowledge check |
| --- | --- | --- | --- | --- | --- |
| M00 | A (roadmap and study guide) | n/a | n/a | n/a | n/a |
| M01 | A | A | A | n/a | A |
| M02 | A | A | A | A | A |
| M03 | A | A | A | A | A |
| M04 | A | A | A | A | A |
| M05 | A | A | A | A | A |
| M06 | A | A | A | A | A |
| M07 | A | A | A | A | A |
| M08 | A | A | A | A | A |
| M09 | A | n/a (script labs) | A | A | A |
| M10 | A | n/a (script labs) | A | A | A |
| M11 | A | n/a (script labs) | A | A | A |
| M12 | A | n/a (script labs) | A | A | A |
| M13 | A | n/a (script labs) | A | A | A |
| M14 | A | n/a (script labs) | A | A | A |
| M15 | A | A | A | A | A |
| M16 | A | A | A | A | A |
| M17 | A | n/a (capstone) | A | A | A |

M02 and M03 are delivered by F03-F10 and F11-F13. Their rows count those units,
including one assessment per unit and a shared synthetic dataset card.

## Release blockers

| Blocker | Why it matters | Resolution |
| --- | --- | --- |
| Licence implementation review | Instructor review of the final implementation report is pending; the terms and files are in place | Not a release blocker; review the report before publication |
| Foundation and section notebooks executed only on Windows 11 CPU | Cross-environment and GPU reproducibility are unverified | Execute representative units on Colab and, where available, a GPU; record the comparison |
| M07/M08 pretrained Hugging Face path not executed | The optional real-model path needs a GPU and a download | Keep the CPU-sized local path mandatory; document the pretrained path as optional |
| Capstone has no sample submission | The three checkpoint gates are specified but untested against a real student package | Run a pilot submission and record the result |
| CI has not run on GitHub | The workflow now covers docs, licensing validation, 253 unit tests, manifest fixtures, projects, generated-data checks, and all 20 notebooks locally, but no Actions runner has executed it | Merge and run the workflow; record the first green run [release audit](../technical/release-readiness-audit.md) |
| No pilot | Time estimates and labs are untested | Run Phase 8 |
| GitHub Pages not enabled | No public site; the deploy workflow cannot publish until the repository setting exists | Set Settings → Pages → Source: GitHub Actions, then run the deploy workflow |
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

1. Execute representative notebooks on Google Colab and record the comparison.
2. Ask a second person to complete an F01-F13 lab and one M04-M16 lab from the published briefs.
3. Reconcile the remote repository if it exists.
4. Review the implemented licensing architecture and final validation report.
5. Run one capstone pilot through the three checkpoints.
6. Run the validation workflow on GitHub Actions and verify the published site.
7. Update this inventory as each artifact changes status.
