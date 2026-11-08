# Release-readiness audit

Audit date: **2026-11-07**. Scope: the complete repository at the working tree
that contains the 18-module curriculum, 20 notebooks, 12 capstone specifications,
eight assessment banks, the P06 deduplication study, and the documentation site.

This audit was performed by an agent. It includes automated execution and an
agent-simulated student journey. **No human student completed the course or the
capstone during this audit.** No GPU, Google Colab, or live GitHub Pages
deployment was verified.

## Verdict

**NOT READY for a public release.**

The curriculum and automated checks are substantially complete, and the
licensing architecture is now **implemented and verified locally**, and the
copyright holder's legal name is **instructor-confirmed**. Three
release-process gates remain: the new CI workflow has **not run on GitHub
Actions**, GitHub Pages is **not verified live**, and no human student pilot has
been completed. These are not evidence that the lessons are wrong. Once those
gates are exercised, the verdict can move to **RELEASE READY WITH WARNINGS**
while the documented environment and upstream-weight limitations remain.

## Baseline before this pass

### What already existed

| Area | Existing check or evidence | Result |
| --- | --- | --- |
| Documentation links | `scripts/check_docs_links.py` checks relative links, heading anchors, and navigation entries | Working |
| Strict documentation build | `mkdocs build --strict` | Working, zero warnings |
| Built-site prefix | `scripts/check_docs_links.py --site site` checks the `/AITopics` project prefix | Working |
| Unit tests | `unittest` suite covering foundations, vision, audio, video, chatbots, agents, LLM fine-tuning, and course projects | 233 tests |
| Project specifications | `scripts/check_course_projects.py` checks 12 specs, rubrics, and eight assessment banks | Working |
| P06 manifest | `scripts/make_vision_data.py --check` verifies the generated set | Working when `data/` exists |
| Notebook execution | All 20 notebooks had been executed on Windows 11 CPU and stored without errors | Historical evidence in the notebooks |
| Deployment | `.github/workflows/deploy-pages.yml` builds, uploads, and deploys after successful validation on `main`, or manual dispatch | Present, never run on GitHub |
| Documentation CI | `.github/workflows/validate-docs.yml` ran links, strict build, and prefix check on documentation-only pull requests | Present, documentation only |

The P06 work is complete and was not repeated: the 57 same-split duplicate
groups, the optional deduplicated set (`objects_p06_dedup`, 902 images), and the
source-balanced experimental set (`objects_p06_balanced`, 240 images) are
documented in the [P06 deduplication study](p06-deduplication-study.md). The
original `objects_p06` dataset and manifest were not modified.

### Missing automated checks found

Before this pass, GitHub Actions did **not**:

- create a Python environment or install the ML dependency sets;
- run `pip check` or the unit suite;
- validate notebook JSON;
- execute any notebook on a CPU kernel;
- validate the P06 or experimental manifests;
- run the project-specification checker;
- run on code-only or notebook-only pull requests.

It also had no licence file and no human usability evidence. The full baseline
inventory is in the [Final repository audit](final-audit.md); this page records
the release decision rather than repeating every historical measurement.

## CI architecture after this pass

The existing documentation workflow was extended rather than duplicated. Its
display name is **Validate repository**, the file remains
`.github/workflows/validate-docs.yml`, and it runs on pull requests targeting
`main`, pushes to `main`, and manual dispatch. Pages deployment waits for a
successful validation run on `main`.

### Python, notebooks, and data job

| Step | Command | What it proves |
| --- | --- | --- |
| Licensing | `python scripts/check_licensing.py` | Legal texts, scope manifest, notices, third-party exclusions, and SPDX consistency are valid |
| Environment | Python 3.12, pip cache keyed to `requirements/*.txt` | The supported interpreter is used |
| Install | `python -m pip install -r requirements/ci.txt` | One reproducible CPU-only union of the foundation, vision, audio, and video sets |
| Dependency consistency | `python -m pip check` | No installed package has a broken requirement |
| Unit tests | `python -m unittest discover -s tests -v` | The full 253-test suite runs, not only the foundation subset |
| Projects | `python scripts/check_course_projects.py` | Twelve project briefs and eight answer-keyed assessment banks are complete |
| Manifest fixture | `python -m unittest tests.test_vision_manifests -v` | Nine tests exercise PASS, FAIL, SKIPPED, missing manifest, corrupt file, invalid label, duplicate warning, and source leakage without the real corpus |
| Manifests | `python scripts/check_vision_manifests.py` | Every present dataset emits PASS or FAIL; a fresh checkout with no `data/` emits SKIPPED, never PASS |
| Notebook JSON | `python scripts/check_notebooks.py --validate` | Every notebook parses, validates, has executed code cells, and stores no error output |
| Notebook execution | `python scripts/check_notebooks.py --execute --timeout 300` | Every notebook runs top-to-bottom on a fresh CPU kernel |
| Kernel | `python -m ipykernel install --user --name python3` | CI can launch the same `python3` kernel students use |

`requirements/ci.txt` composes the existing files; it does not replace or widen
the student dependency sets. CI remains CPU-only, installs no GPU wheel, and
downloads no pretrained model. `MPLBACKEND=Agg`, `HF_HUB_OFFLINE=1`, and
`TRANSFORMERS_OFFLINE=1` keep chart rendering headless and make an accidental
network path fail visibly. No dataset is generated in CI.

### Documentation job

The existing documentation job is preserved: install `requirements/docs.txt`,
check links/anchors/navigation, run `mkdocs build --strict`, then check the built
site for root-absolute URLs that would break under `/AITopics/`.

### Separation from deployment

Validation has `contents: read` only, uploads no artifact, requests no Pages
permission, and cannot publish. Deployment is separate and now waits for a
successful **Validate repository** run on `main` (or explicit manual dispatch),
checking out that run's `head_sha` before building the Pages artifact.

### Local versus GitHub Actions

The workflow was validated locally against the GitHub workflow schema with
`check-jsonschema`. It has **not executed on GitHub Actions** because this task
forbids commit and push. A schema pass proves the YAML is structurally valid; it
does not prove the runner install or notebook execution succeeds. The first
pull-request run after merge is the remaining CI verification step.

## Checks executed in this audit

All commands were run from the repository root on Windows 11 with Python 3.12.10
and the local CPU environment. These are local results, not GitHub Actions
results.

| Check | Exact result |
| --- | --- |
| Unit tests | **253 tests, OK** |
| Licensing validator | **PASS: 8 checks, 0 failures** |
| Licensing tests | **11 tests, OK** (missing file, missing exception, conflicting SPDX, unresolved weights, synthetic attribution, mixed configuration, tampered text, unclassified file, non-content placeholder, overlapping scopes, full repository) |
| Manifest gate tests | **9 tests, OK** (synthetic fixture; no P06 download) |
| Notebook JSON and stored outputs | **20 notebooks valid, 0 errors, 0 unexecuted cells** |
| Notebook execution | **20 notebooks, 169 code cells, 135.2 s locally, 0 failures** |
| P06 original manifest | **960 images, 0 problems, 57 same-split duplicate warnings, no source overlap** |
| P06 deduplicated manifest | **902 images, 0 problems, 0 warnings, no source overlap** |
| P06 balanced manifest | **240 images, 0 problems, 0 warnings, no source overlap** |
| All present vision manifests | **3 datasets, 0 failed, 57 accepted duplicate-content warnings** |
| Project specifications | **12 projects, 12 complete specs, 8 assessment banks with solutions** |
| Markdown links and anchors | **289 Markdown files, 0 broken links or anchors** |
| Strict MkDocs build | **0 warnings** |
| Built site | **288 pages, 0 prefix or broken-asset problems, `/AITopics` prefix** |
| Workflow schemas | **2 workflows and the Dependabot config valid** |
| Dependency consistency | **`pip check` clean; CI requirement resolution has no conflict** |

The generated `data/` directory is git-ignored. The manifest checker therefore
prints **SKIPPED** in a fresh checkout and verifies the datasets only where they
exist. A skip is visible in the CI log and is not reported as a passed dataset
integrity check. The optional complete-data command is:

```bash
python scripts/check_vision_manifests.py --require-datasets
```

That command exits 2 if no dataset is present. CI does not use it because a clean
checkout has no generated data. The nine fixture tests are the reproducible CI
gate for the checker itself. The 57 warnings are the documented byte-identical
variants inside a split; they are not cross-split leakage and are not failed by
CI. See the [P06 deduplication study](p06-deduplication-study.md) for the
controlled comparison that supports keeping `objects_p06` v1.0.0.

## Licensing and attribution

Full detail is in the [Licensing and attribution register](licensing-and-attribution.md),
the [Licensing decision package](licensing-decision-package.md), and
`LICENSES/README.md`. The instructor approved the architecture on 2026-11-07,
and it is implemented in this working tree. The short version:

- **Original source code: MIT.** `LICENSE` contains the complete MIT text with
  the instructor-confirmed copyright holder and year. The scope manifest excludes
  third-party material.
- **Original educational content: CC BY 4.0.** Lessons, documentation, labs,
  notebooks, templates, and diagrams are covered by the complete CC BY 4.0 legal
  code. Commercial reuse is allowed with attribution.
- **Original synthetic data: CC0 1.0.** The provenance record covers deterministic
  generators, including the 960-image P06 set, and the complete CC0 text is
  committed. Third-party data and model checkpoints are excluded.
- **Direct dependencies: Verified for the audited versions.** NumPy, pandas,
  scikit-learn, SciPy, joblib, matplotlib, Pillow, PyTorch, torchvision, OpenCV,
  Jupyter, nbclient, MkDocs, and Material have identifiable open-source licences
  in package metadata. This is not a transitive-dependency audit.
- **Optional Streamlit/sentence-transformers: Pending verification.** They are
  not installed in the audited environment.
- **Pretrained models: Unresolved upstream terms.** No weights are bundled.
  SmolLM2, Qwen, and the torchvision SSDLite COCO weights must be checked against
  their exact model cards. The SSDLite code is BSD-3-Clause, but torchvision does
  not state a separate weight licence; the repository records the weight terms
  as unresolved rather than asserting BSD-3 or Apache-2.0.
- **Bundled third-party media: Not applicable.** No third-party images, audio, or
  video were found; the course generators create the media.

The validator passes locally. This is not a claim that the whole repository is
legally cleared: third-party terms and several upstream items remain unresolved,
as recorded in the register.

## Student journey audit

This is an **agent-based usability audit**, not a human student test. The agent
opened the pages, followed links, inspected the starter files, and executed the
notebooks.

| Step | Result | Finding |
| --- | --- | --- |
| 1. Open the landing page | Pass | README states the audience, scope, cost, prerequisites, and start button |
| 2. Understand prerequisites | Pass | Roadmap has a knowledge, hardware, and software readiness table |
| 3. Follow the roadmap | Pass | Six learning paths and a module map link to published lessons |
| 4. Open the first lesson | Pass | F01 has lesson, notebook guide, lab, and assessment |
| 5. Execute a beginner notebook | Pass locally | F01 needs only the standard library; all 20 notebooks execute on CPU. Colab is documented but was not run |
| 6. Complete a lab | Pass with caveat | F01 has a starter file and rubric; the page states the author did not complete this lab and no solution is published |
| 7. Find an assessment | Pass | Each foundation unit has a self-scored assessment; eight banks have separate solutions |
| 8. Select a capstone | Pass | Twelve specifications are indexed by difficulty, effort, and hardware |
| 9. Find the submission package | Pass | The ten-file scaffold exists at `templates/capstone-submission/` and every project links to the package guide |
| 10. Submit and evaluate the work | Partial | The course is self-study and has no submission channel. Several capstone sentences refer to a "marker" accepting a gate or a "second person" reproducing the result, which implies an instructor or peer that the self-study path does not document |

Other student-facing inconsistencies found:

- **Hardware labels disagree.** The roadmap says M07/M08 are GPU-required and M11
  is GPU-recommended; the lessons index lists M11 as CPU-only and the notebooks
  provide CPU paths. The distinction between the guided CPU notebook and the
  GPU-dependent project is not stated consistently.
- **Capstone language assumes a marker.** The capstone lab says "the marker
  accepts the scope" and "a second person runs the reproduction command." A
  self-directed learner has neither unless they arrange one; the page should say
  self-check or a clean-environment rerun.
- **No human pilot.** The [Capstone pilot report](capstone-pilot-report.md)
  documents an agent-simulated pilot. It is not evidence that a student can
  complete the journey, and this audit does not upgrade it.

No step required an undocumented instructor account, paid API, or private data.
The gaps are wording, optional human review, and unverified external
environments, not hidden setup.

## Known limitations

1. **No human student validation.** No person completed the course, the labs, or
   a capstone under this audit.
2. **No GPU or Colab execution.** The notebooks' GPU branches and the optional
   Hugging Face/PEFT/bitsandbytes path remain unverified.
3. **No live deployment.** GitHub Pages is configured in the workflow but no
   deployment was run or verified here; no public URL is claimed.
4. **No GitHub Actions run.** The workflow passed schema validation and local
   command execution only.
5. **Generated data is absent from a fresh checkout.** `data/` is ignored by
   design; CI checks manifests only when a local generation step has produced
   them.
6. **P06 contains 57 documented same-split duplicate warnings.** They are
   redundancy, not leakage. No dataset was regenerated or modified.
7. **Model performance is not real-world evidence.** The datasets are synthetic
   teaching sets, and the reported metrics describe those sets only.
8. **The Lab 3 computer-vision transfer comparison is unresolved.** The existing
   final audit records a reproducibility problem and a content decision that this
   audit did not change.
9. **Historical results were preserved.** No course metric, pilot number, or P06
   measurement was adjusted.

## Release blockers, prioritized

| Priority | Blocker | Why it blocks release | Owner |
| --- | --- | --- | --- |
| P1 | CI has not run on GitHub Actions | Local success and schema validation do not prove the runner install, kernel, or notebook path | Maintainer |
| P1 | GitHub Pages is not verified live | The course advertises a documentation site but no deployment or URL verification exists | Maintainer |
| P1 | No human usability pilot | The agent journey cannot establish that a student can complete the course | Instructor / reviewer |
| P2 | Hardware labels and capstone "marker" wording are inconsistent | Students may misjudge GPU requirements or wait for a grader who does not exist | Content maintainer |
| P2 | SSDLite weight terms are unresolved | Torchvision licenses the code under BSD-3-Clause but states that pretrained weights may carry dataset-derived terms; no separate weight licence is published | Licence reviewer / instructor |
| P2 | Lab 3 transfer result is not reproducible | The existing audit flags it as a content defect | Content reviewer |
| P3 | No GPU/Colab execution | Optional paths are documented as unverified, but remain unverified | Technical reviewer |

## Recommended remediation sequence

1. **Review and commit the licence implementation.** The licence texts, scope
   manifest, validator, notices, and this audit are prepared in the working tree.
   The instructor should review the final report, then commit them. The licensing
   gate is no longer open, but the SSDLite weight terms remain unresolved.
2. **Merge the validation workflow and let it run on a pull request.** Fix any
   runner-specific failure before calling CI verified. Keep deployment separate.
3. **Enable Pages and verify the deployed site.** Follow the
   [publication guide](GITHUB-PAGES.md), then record the URL and the checks that
   passed. Do not claim a live site before this.
4. **Run one human capstone pilot.** Use the three checkpoint gates and the
   published rubric. Keep the agent pilot separate.
5. **Resolve the content warnings.** Align the hardware table, rewrite the
   capstone "marker" language for self-study, keep SSDLite weights unbundled
   while their terms remain unresolved, and close the Lab 3 reproducibility issue.
6. **Re-run this audit's checks at the release commit** and record the exact
   versions, including a GitHub Actions run and a deployed-site check.

## Reproduction commands

```bash
# Python environment and tests
python -m pip install -r requirements/ci.txt
python -m pip check
python -m unittest discover -s tests -v
python scripts/check_course_projects.py
python -m unittest tests.test_vision_manifests -v   # synthetic manifest fixture
python scripts/check_vision_manifests.py            # SKIPPED without data/
python scripts/check_vision_manifests.py --require-datasets  # optional real-data gate
python scripts/check_notebooks.py --validate
python scripts/check_notebooks.py --execute --timeout 300

# Documentation
python -m pip install -r requirements/docs.txt
python scripts/check_docs_links.py
python -m mkdocs build --strict
python scripts/check_docs_links.py --site site

# Workflow schemas (throwaway environment)
python -m venv tmp/valvenv
tmp/valvenv/Scripts/python -m pip install check-jsonschema
tmp/valvenv/Scripts/check-jsonschema --builtin-schema vendor.github-workflows \
  .github/workflows/deploy-pages.yml .github/workflows/validate-docs.yml
tmp/valvenv/Scripts/check-jsonschema \
  --schemafile https://json.schemastore.org/dependabot-2.0.json .github/dependabot.yml
```

## Final statement

The course content can be followed from F01 to the capstone, and the mandatory
CPU path is now protected by a local validation suite and a whole-repository CI
workflow. The copyright holder is confirmed, but the repository is not
release-ready because remote verification and a human pilot have not happened,
and upstream model-weight terms remain unresolved. No claim is made about human
student success, real-world model performance, GPU/Colab execution, or a live
GitHub Pages site.
