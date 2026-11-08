# Maintainer guide

This guide describes how the course is maintained after the architecture phase.
It is for the instructor, content maintainers, reviewers, and teaching assistants.

## Roles

| Role | Responsibility |
| --- | --- |
| Instructor / owner | Final approval of scope, pedagogy, licensing, and releases |
| Content maintainer | Authors lessons, notebooks, labs, and dataset cards |
| Technical reviewer | Executes notebooks, checks code, reproducibility, and links |
| Pedagogical reviewer | Checks objectives, prerequisites, exercises, and rubrics |
| Ethics and license reviewer | Verifies data, model, privacy, and acceptable use |
| Contributor | Submits corrections, labs, datasets, or documentation improvements |
| Teaching assistant | Supports a cohort, triages issues, and reports recurring problems |

One person may hold several roles, but a module should have at least one reviewer
who did not author it.

## Maintenance cadence

| Frequency | Tasks |
| --- | --- |
| Every pull request | Docs build, targeted tests, link check, review checklist |
| Weekly | Issue triage, broken link reports, dependency alerts |
| Monthly | Merge dependency updates, review open content contributions |
| Quarterly | Execute all published notebooks, check dataset licenses and links |
| Per release | Changelog, tag, known limitations, release notes |
| Annually | License review, roadmap revision, accessibility audit |

## Authoring a module

1. **Confirm the plan.** Update the syllabus page if objectives, hardware, or
   hours change.
2. **Create the lesson folder** at `docs/lessons/mXX-slug/index.md`.
3. **Write the lesson** using the module template in
   [Quality standards](../planning/quality-standards.md).
4. **Write the guided notebook** at `notebooks/<area>/mXX_slug.ipynb`.
5. **Write the lab brief** at `labs/<area>/mXX_slug.md`.
6. **Add dataset and model cards** for anything the learner downloads or uses.
7. **Create the assessment** (knowledge check, rubric evidence, reflection
   prompt).
8. **Execute the notebook** on the stated environments and record the result.
9. **Request reviews** (technical, pedagogical, ethics).
10. **Publish**: add to navigation, update inventory, update the changelog.

Do not publish a lesson and notebook in separate releases unless there is a
documented reason.

## Branch and commit conventions

| Type | Pattern | Example |
| --- | --- | --- |
| Feature/content | `content/short-description` | `content/m07-sft` |
| Fix | `fix/short-description` | `fix/m10-link` |
| Docs | `docs/short-description` | `docs/build-notes` |
| Chore | `chore/short-description` | `chore/bump-mkdocs` |

Commit messages should be short and imperative:

```text
Add M07 SFT lesson and notebook
Fix broken dataset link in M05
Pin mkdocs-material for docs build
```

Review the diff before committing. Never commit data, weights, secrets, or
generated site output.

## Pull request requirements

Every pull request must:

- [ ] State the module or document affected.
- [ ] Explain what changed and why.
- [ ] Include test or execution evidence for notebooks.
- [ ] Pass `mkdocs build --strict`.
- [ ] Pass lint and unit tests when code is changed.
- [ ] Update navigation and inventory for new pages.
- [ ] Include dataset and model license information.
- [ ] Avoid unrelated changes.
- [ ] Disclose substantial AI assistance.

## Notebook execution policy

A notebook is not "done" because it exists.

| State | Requirement |
| --- | --- |
| Draft | May not run completely; not published |
| Executable | Runs top-to-bottom on the author's machine |
| Verified | Runs on the stated primary environment |
| Cross-verified | Runs on Windows 11 and Colab or the documented fallback |
| Published | Verified or cross-verified, with a recorded date and versions |

Record:

- Date and operator.
- Operating system and Python version.
- Key package versions.
- Hardware (CPU, GPU model, VRAM).
- Dataset version and checksum.
- Total runtime.
- Any cells skipped and why.

If a notebook cannot be reproduced, mark it **unverified** and open an issue. Do
not silently leave it online as if it were current.

Every pull request validates and executes all notebooks with
`scripts/check_notebooks.py`. A published notebook must pass both the structural
check and the CPU execution path; the optional GPU or Colab run remains a
separate verification.

## Dataset onboarding

Before a dataset enters the course:

1. Identify the exact source and version.
2. Read the license and acceptable-use terms.
3. Confirm that educational use is allowed.
4. Check for personal, sensitive, or illegal content.
5. Document collection method and consent if human-derived.
6. Record size, schema, splits, and known bias.
7. Create a dataset card and a download script.
8. Add checksums.
9. Confirm that raw data is not committed.
10. Add the dataset to the inventory.

If any step is unclear, do not publish the dataset.

## Model onboarding

Before recommending a model:

1. Record the base model, version, and license.
2. Check the acceptable-use policy, not just the code license.
3. Verify that the model can run within the stated hardware budget.
4. Evaluate it on the lab's task, not only on public benchmarks.
5. Document limitations and failure modes.
6. Confirm that weights are downloaded from an official source.
7. Add a model card and attribution.

Some model licenses restrict commercial use. Mark these clearly and forbid
deployment use in capstone guidance.

## License gate

The course cannot be publicly released without license files.

- Recommended: MIT for code/notebooks, CC BY 4.0 for prose and diagrams.
- The instructor must approve.
- Third-party assets retain their own licenses.
- Contributions should not be accepted at scale until the contribution licensing
  terms are clear.
- If a license is changed, update the README, site footer, and this guide.

## Release checklist

- [ ] All modules in the release satisfy the definition of done.
- [ ] `mkdocs build --strict` passes.
- [ ] Link check passes or exceptions are documented.
- [ ] Notebook execution log is current.
- [ ] Dataset and model licenses are current.
- [ ] No secrets, personal data, or large binaries are tracked.
- [ ] `CHANGELOG.md` and known limitations are updated.
- [ ] Version tag is created after approval.
- [ ] Pages deployment is verified.
- [ ] Rollback commit or procedure is known.

## Incident response

| Incident | Immediate action | Follow-up |
| --- | --- | --- |
| Broken notebook | Mark it unverified; add a warning at the top; open an issue | Fix, execute, record, republish |
| Wrong or harmful content | Remove or unpublish immediately | Notify the instructor; document the review |
| License violation | Remove the asset and related downloads | Audit other uses; update dataset/model cards |
| Secret leaked | Revoke the secret; remove from history with the instructor | Audit logs; add a prevention check |
| Security report | Do not discuss publicly | Follow the private reporting process once `SECURITY.md` exists |
| Site outage | Revert the last deployment commit | Verify Pages status; redeploy |

Do not force-push or rewrite public history without explicit instructor approval.

## Solutions policy

- Guided notebooks are public.
- Lab briefs and rubrics are public.
- Reference solutions are maintainer-only by default.
- Solutions may be released selectively after review.
- Do not link to private solution repositories from public pages.

## Deprecation

When a library, model, or dataset becomes unusable:

1. Mark the lesson as deprecated at the top.
2. State the replacement or the missing capability.
3. Keep the page for a transition period.
4. Remove it from the recommended learning path.
5. Update the inventory and changelog.

## Security and privacy

- Use environment variables or platform secrets; never commit tokens.
- Sandbox agent tools; no real credentials or spending.
- Blur personal data in examples.
- Do not collect student analytics by default.
- Review dependencies for supply-chain risk.
- Keep GitHub Pages permissions minimal.

## Health indicators

Track these without collecting personal data:

- Percentage of published notebooks executed in the last quarter.
- Number of open blocker issues.
- Link checker exceptions.
- Median time to resolve content corrections.
- Pilot completion rate (aggregate, consented).

Avoid vanity metrics such as page views. They do not measure learning.

## Do not

- Do not enable Pages or change remote settings without instructor approval.
- Do not commit datasets, model weights, or secrets.
- Do not publish unverified performance claims.
- Do not add face recognition, covert surveillance, or voice-cloning content.
- Do not rewrite public history or force-push.
- Do not accept large contributions while licensing is unresolved.
- Do not create empty placeholder lessons to make the course look complete.

## Related documents

- [Repository architecture](../planning/repository-architecture.md)
- [Quality standards](../planning/quality-standards.md)
- [Implementation phases](../planning/implementation-phases.md)
- [Build and deploy](build-and-deploy.md)
