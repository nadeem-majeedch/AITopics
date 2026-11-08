# Contributing

Contributions improve the course for everyone. This page explains how to report
problems, propose content, and submit changes without creating legal or technical
problems.

!!! info "Licensing"
    Original code is MIT-licensed, original educational content is CC BY 4.0,
    and verified original synthetic datasets are CC0 1.0. Third-party material
    keeps its upstream terms. Read
    [LICENSES/README.md](https://github.com/nadeem-majeedch/AITopics/blob/main/LICENSES/README.md)
    before reusing or contributing material.

## Ways to contribute

| Contribution | Best channel |
| --- | --- |
| Typo, broken link, unclear explanation | GitHub Issue or small pull request |
| Notebook error or environment failure | GitHub Issue with a minimal reproduction |
| Dataset or model license concern | GitHub Issue marked `license` |
| New lab idea | GitHub Issue first; do not open a large PR |
| New lesson or module | Discuss with the instructor before authoring |
| Accessibility improvement | Pull request or issue |
| Security vulnerability | Follow the private process; do not open a public issue |

## Before you start

1. Read the [Quality standards](../planning/quality-standards.md).
2. Read the [Repository architecture](../planning/repository-architecture.md).
3. Check existing issues to avoid duplication.
4. For anything larger than a correction, open an issue and wait for approval.
5. Do not include personal data, secrets, or unlicensed assets.

## Reporting a problem

Include:

- Module code and page or notebook.
- What you expected.
- What happened, including the exact error.
- Operating system, Python version, and key package versions.
- Hardware: CPU or GPU model, VRAM, Colab/Kaggle if applicable.
- A minimal reproduction, if possible.
- What you already tried.

Do not paste API keys, private datasets, or personal information. Redact paths
that contain your name if you prefer.

## Proposing a lesson or lab

A proposal should answer:

- Which module does it belong to?
- What will the learner be able to do?
- What data will be used, and under what license?
- What hardware is required?
- How will it be evaluated?
- What is the estimated study time?
- What risks or harmful uses must be excluded?

Open an issue with these answers before writing the content.

## Pull request workflow

1. Fork the repository or create a branch if you have write access.
2. Make a focused change.
3. Run the relevant checks:

```bash
python -m mkdocs build --strict
python scripts/check_licensing.py
python -m unittest discover -s tests -v
python scripts/check_notebooks.py --validate
```

4. Add or update tests for code changes.
5. Execute any notebook you changed from a clean kernel.
6. Update navigation and the content inventory for new pages.
7. Open a pull request with a clear description and evidence.
8. Respond to review comments.

Do not include unrelated formatting changes in a content PR.

## Content requirements

- Follow the module template and style guide.
- Use US English.
- Define acronyms on first use.
- Add alt text to images.
- Explain diagrams in text.
- Keep datasets small and legal.
- Add a dataset card and checksums.
- Add a model card for any recommended model.
- State hardware requirements.
- Include evaluation and failure analysis.
- Do not use hype or unsupported claims.
- Do not add emojis.

## Code requirements

- Python 3.11 or 3.12.
- Ruff formatting and linting.
- Type hints for shared package functions.
- Tests for new shared utilities.
- No hard-coded absolute paths or usernames.
- No secrets or personal data.
- No large binaries.

## Notebook requirements

- Runs top-to-bottom from a clean kernel.
- Records environment, hardware, seeds, and runtime.
- Downloads data from official sources.
- Keeps outputs small.
- Clears secrets and private paths.
- States CPU/GPU requirements.
- Is tested on the supported environment.

See [Quality standards](../planning/quality-standards.md#notebook-standards) for
the full checklist.

## Data and model rules

Do not contribute:

- Personal data without documented consent.
- Scraped data that violates terms of service.
- Non-commercial datasets for deployment examples.
- Model weights or datasets in Git.
- Unlicensed images, audio, or video.
- Face recognition, covert surveillance, or non-consensual voice cloning.
- Content that facilitates harm, credential theft, or evasion.

If a license is research-only or non-commercial, mark it clearly and restrict the
example to learning.

## AI assistance

Using AI assistants to draft or review contributions is allowed with disclosure.

In the pull request, state:

- Which tool you used.
- What it helped with.
- How you verified the output.

You are responsible for the correctness, licensing, and safety of everything you
submit. Do not submit fabricated results or citations.

## Review process

| Stage | What reviewers check |
| --- | --- |
| Triage | Scope, duplication, licensing, and fit with the roadmap |
| Technical | Code runs, claims match evidence, no secrets |
| Pedagogical | Objectives, prerequisites, exercises, and rubric alignment |
| Ethics | Data, privacy, bias, and acceptable use |
| Merge | Navigation, inventory, changelog, and release notes |

Review is best effort. A contribution may be declined if it does not fit the
course scope, cannot be verified, or creates legal risk.

## Style

- Use US English.
- Use title case for headings.
- Write directly to the learner as "you".
- Prefer short paragraphs and concrete examples.
- Use code formatting for commands and identifiers.
- Link to primary sources.
- Attribute quotations and figures.

## Commit messages

Use short, imperative messages:

```text
Fix M05 dataset link
Add M10 retrieval evaluation
Clarify GPU requirements in M07
```

## Community expectations

Be respectful, specific, and patient. Critique the work, not the person. Do not
share another learner's work without permission. Harassment and discriminatory
behavior are not tolerated. A formal code of conduct will be added before public
launch.

## Security reports

Do not open a public issue for a vulnerability that could expose users, secrets,
or systems. A private reporting process will be documented in `SECURITY.md`. Until
then, contact the instructor through an institutional channel and avoid public
disclosure.

## Licensing of contributions

Contribute only material you have the right to license. Original code
contributions are accepted under MIT, and original educational content under
CC BY 4.0, consistent with the files they modify. Third-party material must
retain its original licence and attribution; state the source and terms in the
pull request. If you cannot grant these terms, open an issue before investing
significant work.

## Questions

Open a GitHub Issue with the `question` label. Include the module code and what
you are trying to do.
