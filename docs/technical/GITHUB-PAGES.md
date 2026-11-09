# GitHub Pages publication

Maintainer documentation for publishing this course as a **GitHub Pages project
site**. Students do not need this page.

| Item | Value |
| --- | --- |
| Repository | `https://github.com/nadeem-majeedch/AITopics` |
| Framework | MkDocs 1.6 with Material for MkDocs 9.6+ |
| Configuration | `mkdocs.yml` (repository root) |
| Content root | `docs/` |
| Build output | `site/` (git-ignored, never committed) |
| Published URL | `https://nadeem-majeedch.github.io/AITopics/` |
| `site_url` | `https://nadeem-majeedch.github.io/AITopics/` |
| Deployment workflow | `.github/workflows/deploy-pages.yml` |
| PR validation workflow | `.github/workflows/validate-docs.yml` |
| Dependency updates | `.github/dependabot.yml` |

!!! warning "Publication status (verified 2026-11-09)"
    The repository is public and the GitHub API reports
    `default_branch: release/v0.1.0-rc.1` and `has_pages: true`, but
    `GET /repos/nadeem-majeedch/AITopics/pages` returns **HTTP 404** and the
    published URL returns **HTTP 404**. GitHub Actions has **two Dependabot runs
    only**; no validation or deployment workflow has run. The workflows and
    configuration on this page have been validated locally, but the public URL
    must be treated as unverified until a real deployment is inspected. See
    [Verify publication](#verify-publication).

## Release publication procedure (nine steps)

This is the manual sequence for publishing the reviewed release candidate. It is
the only supported path: the working tree is deliberately left uncommitted, and
no agent action commits, pushes, tags, deploys, or changes a repository setting.
Run the commands from the repository root on `release/v0.1.0-rc.1`.

### 1. Review the release diff

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --porcelain=v1 -uall
git diff --stat
git diff --check
git diff --cached --check
```

Expected before the commit: branch `release/v0.1.0-rc.1`, **0 staged paths**, **59
tracked paths** (50 modified, 9 deleted), and **12 untracked files** (the resources
page, the inventory JSON, `labs/README.md`, eight `labs/*/README.md`, and
`tests/test_chatbot_parser_regression.py`). Read the full `git diff`, not only the
stat, and confirm the nine deletions are `labs/*/.gitkeep` placeholders. The
file-by-file inventory is in the [final audit](final-audit.md#release-candidate-snapshot).

### 2. Create the release commit

```bash
git add -A
git diff --cached --stat
git commit -F - <<'MSG'
Repair course navigation and prepare GitHub Pages publication

Add the datasets/resources page, lab READMEs, module links, and notebook
Markdown repairs; widen validation and Pages deployment to release branches;
add inventory floors, JSON output, and parser regression tests.
MSG
git status --porcelain=v1 -uall
git log -1 --format='%H %s'
```

`git add -A` stages the nine `.gitkeep` deletions deliberately; they are empty
placeholders replaced by substantive READMEs. The final `git status` must print
nothing. Record the new commit hash for the next step.

### 3. Push the release branch

```bash
git push origin release/v0.1.0-rc.1
```

The local branch was one commit ahead of `origin/release/v0.1.0-rc.1`; that push
adds the uncommitted repairs as a second commit. Push only this branch. Do not
force-push and do not create a tag or a GitHub release as part of publication.

### 4. Confirm the remote branch has the expected commit

```bash
git fetch origin
git rev-parse HEAD
git rev-parse origin/release/v0.1.0-rc.1
git rev-list --left-right --count origin/release/v0.1.0-rc.1...HEAD
```

Both hashes must match and the last command must print `0	0` (no commits ahead
or behind). A mismatch means the push did not land or ran against another remote;
stop and resolve it before enabling Pages. On the server side:

```bash
gh api repos/nadeem-majeedch/AITopics/branches/release/v0.1.0-rc.1 \
  --jq '.commit.sha'
```

### 5. Set the GitHub Pages source to GitHub Actions

**Settings → Pages → Build and deployment → Source: GitHub Actions.** Do not
choose "Deploy from a branch"; the workflow uploads an artifact and never writes
to `gh-pages`. Equivalent API call, only when Pages has not been created yet:

```bash
gh api -X POST repos/nadeem-majeedch/AITopics/pages \
  -f build_type=workflow
gh api repos/nadeem-majeedch/AITopics/pages --jq '.build_type, .html_url'
```

The second command must report `workflow`; until it does, `configure-pages` fails
with `Get Pages site failed`. Leave **Enforce HTTPS** enabled after the first
deployment.

### 6. Run repository validation

The push itself starts **Validate repository** on `release/v0.1.0-rc.1`:

```bash
gh run list --workflow=validate-docs.yml --branch release/v0.1.0-rc.1 --limit 3
gh run watch <run-id> --exit-status
```

To re-run it without a new commit: `gh workflow run validate-docs.yml --ref
release/v0.1.0-rc.1`. Both jobs (`Python, notebooks, and data`, `Documentation`)
must conclude `success`. This is the first GitHub Actions evidence for the
release; a local pass does not substitute for it.

### 7. Run the Pages deployment

A successful validation on this branch triggers **Deploy documentation** through
`workflow_run`. Check it and, if the automatic run does not appear, dispatch it
explicitly:

```bash
gh run list --workflow=deploy-pages.yml --limit 3
gh run watch <run-id> --exit-status
gh workflow run deploy-pages.yml --ref release/v0.1.0-rc.1   # only if needed
```

The deploy job must show the `github-pages` environment URL. A green build with a
failed or absent deploy job means the Pages source or permissions are wrong, not
that the site is live.

### 8. Verify the public website

```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/course/projects/
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/notebooks/production/m16_production/
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/sitemap.xml
curl -sS https://nadeem-majeedch.github.io/AITopics/ | grep -o '<link rel="canonical"[^>]*>'
gh api repos/nadeem-majeedch/AITopics/pages --jq '.status, .html_url'
```

All four codes must be `200`, the canonical link must contain
`https://nadeem-majeedch.github.io/AITopics/`, and the Pages API must no longer
return 404. Only then is the site published; record the run id and the commit SHA
it deployed in the [verification log](build-and-deploy.md#verification-log).

Notebook pages embed their executed `.ipynb` as a download (`mkdocs-jupyter`
`include_source: true`). No notebook SHA-256 manifest is committed, so verify a
download against the repository copy instead:

```bash
curl -sS -o tmp/m16_download.ipynb \
  https://nadeem-majeedch.github.io/AITopics/notebooks/production/m16_production/m16_production.ipynb
sha256sum tmp/m16_download.ipynb notebooks/production/m16_production.ipynb
```

(The Windows equivalent is `certutil -hashfile <file> SHA256`.) The two hashes must
match; if they do not, the deployed commit is not the reviewed commit.

### 9. Test the site in a clean browser session

Use a private/incognito window with an empty cache — not the session that built
the site — and check:

1. The home page renders styled, with the tabs bar and the search box.
2. **Notebook Library → M16 - Evaluation and serving** renders code and outputs,
   and its download link returns the `.ipynb` file rather than a 404.
3. A deep page such as **Capstone projects → Project index** loads, and the
   sidebar's module links resolve rather than pointing at GitHub `main`.
4. Search returns results for `LoRA` and `tracking`.
5. A deliberately wrong path such as `/AITopics/no-such-page/` shows the site's
   own 404 page, not GitHub's generic one.
6. **Edit this page** opens the file on `release/v0.1.0-rc.1` (the configured
   `edit_uri`), not a 404.
7. At a narrow viewport (about 390 px) the navigation collapses into a usable
   menu instead of overflowing.

Record what you saw, and anything you could not check, in the verification log.
Do not describe the site as verified for students on the strength of a 200
response alone.

## Why the base path matters

This is a **project site**, not a user site, so every published URL lives under
the repository prefix:

```text
https://nadeem-majeedch.github.io/AITopics/
```

Two things must agree with that prefix:

1. **`site_url` in `mkdocs.yml`.** It sets canonical URLs, the sitemap, and the
   Open Graph metadata. Without it MkDocs emits URLs rooted at the domain and the
   sitemap points at the wrong location.
2. **Page and asset URLs inside the HTML.** MkDocs writes **relative** URLs
   (`../../assets/stylesheets/main.css`), which resolve correctly under any
   prefix. A hand-written root-absolute link such as `/course/roadmap.md` would
   break, because the browser would request `https://nadeem-majeedch.github.io/course/...`
   instead of `/AITopics/course/...`.

The source has no root-absolute internal links. `scripts/check_docs_links.py`
fails the build if one appears, either in Markdown or in the generated HTML. It
does accept absolute URLs that already carry the `/AITopics` prefix, because
MkDocs writes those into `404.html` deliberately: that page is served at
arbitrary depths and cannot use relative URLs.

Do not set `use_directory_urls: false` to work around a prefix problem. The
relative-URL scheme already handles the prefix; changing that setting alters
every published URL.

## Prerequisites

- Maintainer access to the repository (to merge the release branch and to change
  Pages settings once).
- The repository default branch is **`release/v0.1.0-rc.1`**. Both workflows
  trigger on `main` and `release/**`; `edit_uri` points at the current release
  branch and must be updated after a merge to `main`.
- GitHub Actions enabled for the repository.
- GitHub Pages available for this repository. Pages is free for public
  repositories; for a private repository the account plan must include Pages.
  If **Settings → Pages** offers no source option, confirm visibility and plan
  before debugging the workflow.
- No secrets. The build installs two public packages and deploys a public static
  site; it needs no tokens, API keys, or environment variables.

Local prerequisites for reproducing the build:

- Python 3.12 (3.11 also works; CI uses 3.12).
- `requirements/docs.txt` (MkDocs and Material only, no ML dependencies).

## Build command

From the repository root, in a virtual environment:

```bash
python -m pip install -r requirements/docs.txt
python scripts/check_docs_links.py
python -m mkdocs build --strict
python scripts/check_docs_links.py --site site
```

- `--strict` turns MkDocs warnings into errors, so a missing nav file or a bad
  page fails the build locally exactly as it would in CI.
- The output is `site/`. It is git-ignored; do not commit it.
- The link checker also verifies heading anchors and every `nav` entry.

## Local preview

```bash
python -m mkdocs serve
```

Open `http://127.0.0.1:8000/`. The preview serves at the domain root, so it does
**not** exercise the `/AITopics/` prefix. To test the prefix, serve the built
output under a directory named `AITopics`:

```bash
python -m mkdocs build --strict
mkdir -p tmp/pages-sim/AITopics
cp -r site/. tmp/pages-sim/AITopics/
cd tmp/pages-sim && python -m http.server 8765
```

Then open `http://127.0.0.1:8765/AITopics/` and check a nested page such as
`http://127.0.0.1:8765/AITopics/course/projects/`. `tmp/` is git-ignored.

## Repository settings required

These are one-time, manual, administrator actions. They cannot be set from this
repository and must not be changed by automation.

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
   Do not choose "Deploy from a branch"; the workflow uploads an artifact rather
   than committing to `gh-pages`.
2. Confirm the default branch is `release/v0.1.0-rc.1`
   (**Settings → General → Default branch**), or update `mkdocs.yml`, the Colab
   links, and the workflow triggers if it changes.
3. Leave **Enforce HTTPS** enabled after the first deployment.
4. Do not add a custom domain unless the course owner decides to. If one is
   added, `site_url` must change and the CNAME file becomes part of the build.
5. Optional: under **Settings → Environments → github-pages**, restrict who may
   deploy. The environment is created by the first deployment; no secrets belong
   in it.

No repository secret is required, and none should be added for this workflow.

## Workflow behaviour

### `deploy-pages.yml` — Deploy documentation

| Property | Value |
| --- | --- |
| Triggers | successful **Validate repository** run on `main` or `release/**` (`workflow_run`); `workflow_dispatch` |
| Permissions (top level) | `contents: read` |
| Permissions (deploy job) | `pages: write`, `id-token: write` |
| Concurrency | group `pages`, `cancel-in-progress: false` |
| Build job | check out the validated run's `head_sha` → Python 3.12 with pip cache → install docs deps → link/anchor/nav check → `mkdocs build --strict` → built-site prefix check → `actions/configure-pages` → `actions/upload-pages-artifact` (`site`) |
| Deploy job | needs build → `actions/deploy-pages` in the `github-pages` environment |

The deploy job does not run on pull requests. The build job checks out the
validated commit and does not modify the repository; the artifact is the static
`site/` directory. A successful push validation is therefore the normal
deployment gate, while manual dispatch remains an explicit maintainer action.

Actions used: `actions/checkout@v4`, `actions/setup-python@v5`,
`actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`,
`actions/deploy-pages@v4`. They are pinned to major versions, which is the
standard GitHub-maintained pattern; pin to a commit SHA instead if the owner
requires it.

### `validate-docs.yml` — Validate repository

The file name is historical; the workflow now covers the whole repository.

| Property | Value |
| --- | --- |
| Triggers | pull requests targeting `main` or `release/**`; pushes to `main` or `release/**`; `workflow_dispatch` |
| Permissions | `contents: read` only |
| Concurrency | per-ref, `cancel-in-progress: true` |
| Python job | install `requirements/ci.txt`, `pip check`, licensing validation, 269 unit tests, a synthetic manifest fixture, project checks, generated-data check, notebook JSON validation, and execution of all 26 notebooks |
| Documentation job | install docs dependencies, link/anchor/nav check, strict build, and prefix check |
| Pages actions | none; no artifact upload, no deployment job |

This is the gate that catches a broken link, failed test, invalid notebook, or
manifest problem **before** merge or deployment. A fork pull request cannot
publish anything because it has no Pages permission and no deployment job. A
direct push to `main` or a release branch is validated too; Pages deployment
waits for the successful run instead of starting from the push itself.

### Dependency updates

`.github/dependabot.yml` opens monthly pull requests for `mkdocs`,
`mkdocs-material`, and the GitHub Actions used by these workflows. Each PR runs
`validate-docs.yml`. Dependabot does not update the ML dependency sets; update
them deliberately because notebook execution depends on the resolved CPU stack.

### Validating these files before committing

A YAML parse alone does not prove a workflow is valid. Validate against the
published schema instead, in a throwaway environment:

```bash
python -m venv tmp/valvenv
tmp/valvenv/Scripts/python -m pip install check-jsonschema
tmp/valvenv/Scripts/check-jsonschema --builtin-schema vendor.github-workflows \
  .github/workflows/deploy-pages.yml .github/workflows/validate-docs.yml
tmp/valvenv/Scripts/check-jsonschema \
  --schemafile https://json.schemastore.org/dependabot-2.0.json .github/dependabot.yml
```

All three files validate as of 2026-11-09, after the release-branch trigger and
`edit_uri` changes. `tmp/` is git-ignored, so the virtual environment and any
incident artifacts stay out of the repository.

## Expected published URL

```text
https://nadeem-majeedch.github.io/AITopics/
```

Sitemap: `https://nadeem-majeedch.github.io/AITopics/sitemap.xml`

The first deployment can take a few minutes to become reachable; later
deployments usually replace content within a minute. If the URL returns 404 after
a successful run, check the Pages source setting and the environment URL reported
by the deploy job.

## Inspect build and deployment failures

1. **Actions tab → Deploy documentation → the run.** The failing step is marked
   in red; expand it for the log.
2. **Locally reproduce the failing step.** A strict-build failure names the file
   and the warning:

   ```bash
   python -m mkdocs build --strict
   ```

   A link failure names the page and the target:

   ```bash
   python scripts/check_docs_links.py
   ```

3. **Download the artifact** from the run summary to inspect exactly what was
   built (`github-pages` artifact).
4. **Deploy-job failures** are usually permissions, environment protection, or
   Pages settings. Read the `actions/deploy-pages` step log; it reports the HTTP
   status from the Pages API.
5. With the GitHub CLI:

   ```bash
   gh run list --workflow=deploy-pages.yml
   gh run view <run-id> --log-failed
   gh run watch <run-id>
   ```

### Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Aborted with a BuildError` / warnings as errors | Missing nav target, bad page, duplicate anchor | Run the strict build locally; fix the named file |
| Link check fails | Relative link typo, missing heading anchor, root-absolute link | Run `check_docs_links.py`; use a relative `.md` link |
| Deploy job fails with 403/404 from Pages | Pages source not set to GitHub Actions, or Pages disabled | Settings → Pages → Source: GitHub Actions |
| `Get Pages site failed` | Pages not enabled for the repository | Enable Pages, then re-run the workflow |
| Environment waiting for approval | Protection rule on `github-pages` | Approve the deployment, or relax the rule deliberately |
| Deployment does not run after a push | Validation did not finish successfully, wrong branch, or Actions/Pages disabled | Check the Validate repository run and the default branch |
| Site loads unstyled or 404s assets | A root-absolute asset URL was introduced | Run `check_docs_links.py --site site` |
| Old content after a successful run | CDN/propagation delay, or the run deployed from another branch | Wait, then compare the run's commit SHA with the validated branch |

## Verify publication

Run these **after** a real workflow run has succeeded. Do not report the site as
published based on the workflow file alone.

```bash
# 1. The deployment run succeeded and deployed the expected commit
gh run list --workflow=deploy-pages.yml --limit 3
gh run view <run-id> --json conclusion,headSha,url

# 2. The site answers with 200 at the project prefix
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/

# 3. A nested page and an asset answer with 200 (not the GitHub 404 page)
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/course/projects/
curl -sS -o /dev/null -w "%{http_code}\n" https://nadeem-majeedch.github.io/AITopics/sitemap.xml

# 4. The HTML points at the correct canonical URL
curl -sS https://nadeem-majeedch.github.io/AITopics/ | grep -o '<link rel="canonical"[^>]*>'

# 5. The stylesheet referenced by the page loads
curl -sS https://nadeem-majeedch.github.io/AITopics/ | grep -o 'href="[^"]*main[^"]*\.css"'
```

In a browser, confirm: the home page is styled, search returns results, the
sidebar and tabs work, a deep page such as **Capstone projects → Project index**
renders, and the 404 page is the site's own page rather than GitHub's generic one.

Record the verification in the log in
[Build and deploy](build-and-deploy.md#verification-log) only after running it.

## Related documents

- [Build and deploy](build-and-deploy.md) — framework, local setup, conventions
- [Site maintenance](site-maintenance.md) — dependency updates and local validation
- [Maintainer guide](maintainer-guide.md) — review and release process
- [Troubleshooting](troubleshooting.md) — MkDocs, Python, and Windows issues
