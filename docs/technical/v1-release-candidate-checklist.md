# v1 release-candidate checklist

**Status: READY FOR GITHUB VALIDATION. Release verdict: NOT RELEASE READY.**
The working tree is licensing- and validation-complete locally, and the
copyright holder is instructor-confirmed. It has not yet passed GitHub Actions,
GitHub Pages deployment, or an independent human student pilot, and upstream
weight terms remain unresolved.

**Prepared:** 2026-11-07; **updated:** 2026-11-08  
**Licensing status:** `LICENSING IMPLEMENTED WITH WARNINGS`  
**Recommended first tag:** `v0.1.0-rc.1` (candidate), then `v0.1.0` after the
external checks pass. Do not use `v1.0.0` until a human student pilot and a
stable curriculum review are complete.

This page is not legal advice. It records what has and has not been verified.

## 1. Completed work

| Area | Evidence | Status |
| --- | --- | --- |
| Copyright holder | Instructor confirmed **Muhammad Nadeem Majeed**; MIT line uses that exact name | **Confirmed** |
| MIT text for original code | `LICENSE`, exact 162-word body and copyright line | **Verified** |
| CC BY 4.0 text | `LICENSES/CC-BY-4.0.txt`, exact official text and SHA-256 | **Verified** |
| CC0 1.0 text | `LICENSES/CC0-1.0.txt`, exact official text and SHA-256 | **Verified** |
| Public licence map | `LICENSES/README.md`, scope and attribution wording | **Complete** |
| Synthetic-data provenance | `LICENSES/SYNTHETIC-DATA.md`, nine generators and P06 record | **Complete** |
| Machine-readable scopes | `licensing-scope.json`, four scopes and five third-party exclusions | **Complete** |
| Repository-wide coverage | `scripts/check_licensing.py`, all 572 release files classified | **Passing locally** |
| Regression tests | `tests/test_licensing.py`, 11 tests including coverage gaps | **Passing locally** |
| CI gate | `.github/workflows/validate-docs.yml`, no Pages permissions; PR, `main` push, and manual dispatch | **Configured; not run on GitHub** |
| Documentation build | Strict MkDocs build and built-site prefix check | **Passing locally** |
| Historical data/results | No historical experiment result or dataset modified | **Preserved** |

## 2. Outstanding warnings

| Warning | Why it remains | Owner | Release effect |
| --- | --- | --- | --- |
| SSDLite COCO weight terms | Torchvision states no separate weight licence; terms may inherit COCO-derived restrictions | Instructor / licence reviewer | **Warning; weights unbundled** |
| Optional model revisions | SmolLM2, Qwen, torchvision ImageNet, ASR/TTS models are not pinned to audited revisions | Maintainer / student | **Warning; no weights bundled** |
| Fine-tuned checkpoints | A checkpoint derived from third-party weights may inherit restrictions | Maintainer / student | **Do not redistribute without review** |
| External dataset terms | COCO image-level terms, DeepFashion, UCF101, and student datasets remain upstream | Student / instructor | **Warning** |
| Code-similarity audit | No copied code was identified by marker search, but no similarity audit was performed | Maintainer | **Warning** |
| GitHub Actions | No workflow has run on GitHub because nothing was committed or pushed | Maintainer | **Blocking verification** |
| GitHub Pages | Deployment workflow exists, but the live site has not been published or checked | Maintainer | **Blocking verification** |
| Human student pilot | The capstone pilot is explicitly agent-simulated, not a human student pilot | Instructor | **Blocking release claim** |

## 3. Licensing status

The final licensing verdict is **`LICENSING IMPLEMENTED WITH WARNINGS`**:

- the exact legal texts match their official sources;
- the instructor-confirmed copyright line and SPDX identifiers are consistent;
- the release tree is fully classified, with no overlaps;
- third-party material is excluded and not relicensed;
- generated data is explicitly git-ignored;
- the SSDLite code/weights distinction is stated;
- the remaining warnings are external facts, not missing repository files.

See the [Independent final licensing audit](final-licensing-audit.md), [Scope
coverage](licensing-scope-coverage.md), and [Third-party
inventory](third-party-inventory.md).

## 4. CI verification status

The workflow is statically valid (`check-jsonschema` 0.39.0), runs on pull
requests targeting `main`, pushes to `main`, and manual dispatch, and covers:

| Required check | Workflow step | Local status |
| --- | --- | --- |
| Unit tests | `python -m unittest discover -s tests -v` | **269 tests, OK** |
| Licensing validator | `python scripts/check_licensing.py` | **PASS, 8 checks** |
| P06 manifest fixture | `python -m unittest tests.test_vision_manifests -v` | **Passing** |
| Vision dataset manifests | `python scripts/check_vision_manifests.py` | **3 datasets PASS; 57 duplicate warnings** |
| Course projects | `python scripts/check_course_projects.py` | **12 projects, 12 complete specs, 8 banks** |
| Notebook JSON validation | `python scripts/check_notebooks.py --validate` | **26 notebooks valid** |
| Notebook execution | `python scripts/check_notebooks.py --execute --timeout 300` | **20 executed, 0 failures** |
| Documentation links | `python scripts/check_docs_links.py` | **Passing locally** |
| Strict MkDocs build | `python -m mkdocs build --strict` | **Passing locally** |
| Built-site prefix | `python scripts/check_docs_links.py --site site` | **Passing locally** |
| No deployment | No `pages: write` or deploy action in `validate-docs.yml` | **Verified** |

**Local environment caveat:** the audit environment did not have `torchvision`
or the optional LLM packages, and its OpenCV wheel (5.0.0.93) is newer than the
`<5` requirement cap. The local suite and notebooks pass, but the fresh CI
resolution must be the release evidence; do not treat the local wheel set as an
exact reproduction of CI.

**Validation and deployment sequencing:** validation now runs on a direct push
to `main` as well as on pull requests and manual dispatch. `deploy-pages.yml` is
separate and triggers on successful completion of **Validate repository** on
`main`, plus manual dispatch. The build checks out the validated run's
`head_sha`, so a docs push cannot publish before validation. A manual deployment
dispatch can still be started before validation; the maintainer procedure below
requires a green validation run first. Repository branch-protection settings are
not assumed and must be verified by the instructor.

## 5. First GitHub Actions run: maintainer checklist

Run these in order after the instructor authorises the commit and push:

- [ ] Confirm the working tree contains the licence files, manifest, validator,
      tests, and documentation changes; do not commit generated data or caches.
- [ ] Prefer a pull request; a direct push to `main` now also starts validation.
- [ ] If using manual dispatch, run **Actions → Validate repository → Run
      workflow** and record the run.
- [ ] Confirm the `Python, notebooks, and data` job starts and installs
      `requirements/ci.txt`.
- [ ] Confirm `Check dependency consistency` reports no broken requirements.
- [ ] Confirm the licensing step prints **PASS** and the coverage line reports
      every release file classified.
- [ ] Confirm the licensing tests and the full unit suite pass.
- [ ] Confirm the P06 fixture, vision manifests, and course-project checks pass.
- [ ] Confirm all 26 notebooks validate and execute within the 25-minute job
      timeout.
- [ ] Confirm the documentation job checks links, builds with `--strict`, and
      passes the `/AITopics` prefix check.
- [ ] Confirm the validation workflow did **not** deploy or request Pages
      permissions.
- [ ] Record the run URL, commit SHA, date, and any warning output in the release
      record.
- [ ] Only after a green validation run, run the separate Pages deployment
      workflow and verify the published site, including a deep link under
      `/AITopics/`.
- [ ] Do not label the repository `RELEASE READY` or create `v1.0.0` until the
      human pilot and approvals below are recorded.

## 6. Pages deployment status

- Workflow: `.github/workflows/deploy-pages.yml`.
- Trigger: successful completion of **Validate repository** on `main`, or manual
  dispatch. Pull requests do not deploy.
- Permissions: build job reads contents; deploy job has `pages: write` and
  `id-token: write`.
- Current state: **not deployed and not verified live**.
- Validation gate: the workflow waits for a successful validation run and checks
  out that run's `head_sha`; it no longer deploys directly from a docs push.
- Residual risk: manual deployment dispatch is still an explicit maintainer
action and can be started without a green run; follow the checklist above.
- Required post-deploy check: open the published URL, verify the project prefix,
  navigation, a lesson page, a notebook page, and the licensing pages; check the
  browser console and network responses.

## 7. Human student pilot status

- **No human student pilot has been completed.**
- `docs/technical/capstone-pilot-report.md` is an **agent-simulated** pilot. It
  tests whether the briefs and code are executable; it is not a human rubric
  score, a human approval test, or evidence of learning outcomes.
- A release claim that says "student-validated" would be unsupported until at
  least one human student completes the beginner path and the instructor records
  the result. Use the [student pilot protocol](student-pilot-protocol.md); do not
  substitute the agent-simulated capstone report.
- The [draft rc.1 release notes](release-notes-v0.1.0-rc.1.md) must keep the pilot
  status explicit.

## 8. Known model and dataset limitations

| Limitation | Effect |
| --- | --- |
| Most core data is synthetic | Results demonstrate mechanics, not real-world accuracy |
| SSDLite COCO zero-shot performance is poor on the synthetic traffic domain | The detector is a baseline, not a deployable traffic system |
| No real human speech, images, or video in the mandatory path | Privacy and consent risks are reduced, but external validity is limited |
| Optional GPU/pretrained paths were not executed | Do not claim GPU, LoRA, or real-model quality results |
| The capstone pilot is agent-simulated | No human usability or assessment evidence |
| External datasets and weights remain upstream-controlled | Redistribution and commercial-use answers depend on the user's exact source |

## 9. Required release approvals

- [x] Instructor confirms the copyright holder's exact legal name:
      Muhammad Nadeem Majeed.
- [ ] Instructor approves the final licensing status and this checklist.
- [ ] Licence reviewer either resolves the SSDLite COCO weight terms or confirms
      that the weights and derivatives remain unbundled and unresolved.
- [ ] Maintainer records a green GitHub Actions validation run.
- [ ] Maintainer publishes and verifies GitHub Pages.
- [ ] Instructor completes or explicitly defers a human student pilot, and the
      release notes state which claim is not yet supported.
- [ ] Maintainer confirms no generated data, caches, model weights, or secrets
      are in the release commit.

## 10. Recommended versioning approach

1. **`v0.1.0-rc.1`** after local validation and the first green CI run, while the
   human pilot and SSDLite weight review are outstanding.
2. **`v0.1.0`** after the approvals above and a verified Pages deployment.
3. **`v1.0.0`** only after a human student pilot, a stable curriculum review, and
   an explicit decision that the course content is no longer experimental.
4. Use annotated Git tags and a short release note listing the licensing status,
   the unresolved SSDLite weight terms, and the exact validation run.
5. Keep the documentation version and the package/release tag aligned; do not
   imply that a docs deployment alone is a software release.
6. Record the candidate in the [draft release notes](release-notes-v0.1.0-rc.1.md)
   and remove the draft label only after the external checks pass.

The working tree is **READY FOR GITHUB VALIDATION**. The repository remains
**NOT RELEASE READY** until every blocking item in sections 2 and 9 is closed or
explicitly accepted by the instructor.
