# Draft release notes — v0.1.0-rc.1

**Status: release-candidate draft, not a published release.** Local validation
passed with documented limitations on 2026-11-08. The tag has not been created,
the repository has not been pushed for this candidate, GitHub Actions has not run
the validation or deployment workflow, GitHub Pages has not been published, and no
human student pilot has been completed. Do not describe this draft as a verified
public release.

**Candidate version:** `v0.1.0-rc.1`  
**Prepared:** 2026-11-08  
**Release gate:** [v1 release-candidate checklist](v1-release-candidate-checklist.md)

## Course overview

AITopics is a self-paced, hands-on course on training, fine-tuning, evaluating,
and deploying language, vision, speech, video, and agentic AI systems. It is
written for undergraduate and postgraduate students, developers moving into AI,
researchers who need practical lifecycle skills, and instructors who want a
modular applied curriculum.

The course starts with Python and classical machine learning, then builds through
deep learning, small language models, retrieval-augmented chatbots, computer
vision, speech and audio, video analytics, tool-using agents, production
evaluation, and an integrated capstone. The emphasis is on reproducible evidence:
a baseline, a measured comparison, an error analysis, a data or model card, and a
documented limitation.

Prior knowledge: basic Python, a terminal, and high-school algebra. Prior deep
learning experience is not required.

## What is included

| Area | Coverage |
| --- | --- |
| Curriculum | 18 modules, with the foundation sequence F01–F13 delivering M01–M03 |
| Notebooks | 26 executable notebooks: 13 foundation and 13 module notebooks |
| Notebook library | Direct links to all 26 notebooks, with rendered pages and downloadable sources |
| Labs | Independent lab briefs with rubrics, including the F01 toolkit lab |
| Applied sections | Model training, LLM fine-tuning, conversational AI, computer vision, speech and audio, video AI, agents, and production |
| Capstones | 12 fully specified projects, from a tabular baseline to a tool-using agent with approvals |
| Assessment | Eight assessment banks with separate self-study solutions |
| Documentation | A MkDocs site with lessons, labs, projects, licensing, and maintenance pages |

The mandatory core path is CPU-oriented. Some optional model-training and
pretrained-model paths are labelled GPU recommended or GPU required; those paths
were not executed on GPU for this candidate.

## Licensing model

Original material is multi-licensed; no single licence covers every file.

| Material | Licence |
| --- | --- |
| Original source code, tests, scripts, and build configuration | MIT |
| Original lessons, documentation, labs, notebooks, templates, and diagrams | CC BY 4.0 |
| Original synthetic datasets, after provenance review | CC0 1.0 |
| Third-party code, data, media, and model weights | Their original upstream terms |

The copyright holder is **Muhammad Nadeem Majeed**, confirmed by the instructor.
The MIT notice reads `Copyright (c) 2026 Muhammad Nadeem Majeed`.

Commercial reuse of original educational content is permitted under CC BY 4.0
with attribution, a link to the licence, and an indication of changes. The
licence does not grant rights to third-party material.

See [`LICENSES/README.md`](https://github.com/nadeem-majeedch/AITopics/blob/main/LICENSES/README.md),
[`licensing-scope.json`](https://github.com/nadeem-majeedch/AITopics/blob/main/licensing-scope.json),
and the [third-party inventory](third-party-inventory.md) for the exact scope and
exclusions. This summary is not legal advice.

## Hardware and software

| Resource | Expectation |
| --- | --- |
| Operating system | Windows 11 or Linux; Google Colab is documented for optional GPU work |
| Python | 3.11 or 3.12 recommended; F01 needs only the standard library |
| RAM | 8 GB minimum; 16 GB or more recommended |
| Disk | 30 GB free minimum; 60 GB recommended for optional datasets and weights |
| GPU | None for the CPU core path; an NVIDIA GPU with 8 GB+ VRAM is useful for optional training |
| Accounts | GitHub and a notebook environment; Colab, Kaggle, and Hugging Face are optional |

Dependency ranges are in `requirements/`. The CI environment installs the
CPU-only union from `requirements/ci.txt`; do not assume that the local audit
wheel set is an exact reproduction of CI.

## Reproducibility notes

- Every notebook is stored with its outputs and was executed top to bottom on a
  Windows 11 CPU environment during the local audit.
- The final local audit executed 26 notebooks and 223 code cells in 176.1
  seconds with zero failures. This is a local result, not a GitHub Actions
  result.
- The deterministic chatbot/RAG parser was repaired on 2026-11-08: instruction
  text is no longer treated as part of the question, and support now requires
  meaningful evidence overlap. All 253 unit tests pass.
- Generated data is git-ignored; the deterministic generators and seeds are
  recorded in [`LICENSES/SYNTHETIC-DATA.md`](https://github.com/nadeem-majeedch/AITopics/blob/main/LICENSES/SYNTHETIC-DATA.md).
- Synthetic data is generated locally rather than downloaded. No dataset,
  checkpoint, or pretrained weight is bundled in the release tree.
- The course records commands, seeds, environment details, and measured hardware
  where a result depends on them.
- Optional GPU, Colab, hosted-API, and pretrained-model paths are labelled
  optional and are not claimed as verified by this candidate.

## Known limitations

- Most mandatory data is synthetic. Results demonstrate mechanics and evaluation
  discipline, not real-world accuracy.
- The SSDLite COCO detector is a baseline; zero-shot performance on the synthetic
  traffic domain is poor.
- No real human speech, images, or video are required in the mandatory path, which
  reduces privacy risk but limits external validity.
- The capstone pilot in the repository is agent-simulated, not a human student
  pilot. It is not evidence of learning outcomes or usability.
- GPU, Google Colab, and optional hosted models were not verified for this
  candidate.
- The 20 pre-existing notebooks do not all follow the 14-section template used
  by the six applied notebooks added for M09-M14.
- The course is self-study; it does not provide a submission channel, graded
  credential, or guaranteed marker.
- No code-similarity audit was performed. External references are cited, but the
  project does not claim a complete originality audit.

## Third-party model and dataset restrictions

- No third-party dataset, media file, or model weight is redistributed.
- SSDLite **code** is BSD-3-Clause. The SSDLite **COCO weights** have no separate
  licence stated by torchvision and remain **unresolved**; do not relabel them as
  MIT, BSD-3-Clause, or Apache-2.0.
- SmolLM2 and Qwen are optional upstream models. Check the exact model card,
  revision, licence, and terms before use or redistribution.
- COCO, CIFAR-10, Fashion-MNIST, DeepFashion, TinyShakespeare, Speech Commands,
  LibriSpeech, Common Voice, and UCF101 remain subject to their upstream terms
  when a student downloads them.
- Fine-tuned checkpoints derived from third-party weights may inherit
  restrictions. Do not publish a checkpoint without a separate review.
- Optional packages such as Streamlit, sentence-transformers, and ASR/TTS stacks
  are installed separately under their own licences.

## Release-candidate verification status

| Check | Status |
| --- | --- |
| Local Python suite | 253 tests passed |
| Licensing validator | PASS, 8 checks, 560 release files classified |
| Notebook validation | 26 notebooks valid |
| Notebook execution | 26 notebooks, 223 code cells, 176.1 s, 0 failures |
| P06 fixture | 9 tests passed |
| Course inventory | 18 modules, 105 lesson files, 26 notebooks, 52 labs/project briefs, 21 assessments |
| Course projects | 12 projects, 12 complete specifications, 8 assessment banks |
| Markdown links and anchors | 295 Markdown files resolve |
| Strict MkDocs build | 322 pages, 0 warnings |
| Built-site `/AITopics` prefix | 322 pages, no prefix or broken-link problems |
| Workflow schemas | Valid with `check-jsonschema` 0.39.0 |
| GitHub Actions | **Not run; 2 Dependabot runs only** |
| GitHub Pages | **HTTP 404; not published or verified live** |
| Human student pilot | **Not completed**; protocol prepared |
| SSDLite weight terms | **Unresolved** |

These are local results. They do not establish that a GitHub runner, a student,
or the public Pages site works.

## Feedback and issue reporting

Open an issue at <https://github.com/nadeem-majeedch/AITopics/issues> for a broken
link, setup failure, unclear instruction, or incorrect result. Include the page
or notebook path, the command, the Python and operating-system versions, and the
exact error text. Do not include tokens, personal data, real inbox content, or
private dataset material in a public issue.

For a course usability problem, use the [student pilot
protocol](student-pilot-protocol.md) as the observation template. For a licensing
question, identify the file and the exact upstream source; do not infer a licence
from a filename or a project's general licence.

## Before tagging this candidate

- [ ] Instructor reviews and approves the final licensing status and checklist.
- [ ] A pull request or `main` push runs **Validate repository** successfully.
- [ ] The Pages deployment is run only after a green validation and is verified
      at `https://nadeem-majeedch.github.io/AITopics/`.
- [ ] The instructor records whether the SSDLite weight terms are resolved or
      explicitly remain unbundled and unresolved.
- [ ] A human student pilot is completed, or the release note explicitly states
      that it was deferred.
- [ ] No generated data, cache, checkpoint, or secret is included in the release
      commit.

Until those checks are complete, this is a **draft for the first release
candidate**, not a released version.
