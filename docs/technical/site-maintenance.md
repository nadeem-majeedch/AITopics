# Site maintenance

Short, technical maintenance routine for the documentation site. Students do not
need this page. For publication mechanics see [GitHub Pages](GITHUB-PAGES.md);
for the full review process see the [Maintainer guide](maintainer-guide.md).

## Routine

| When | Do this |
| --- | --- |
| Before every documentation commit | Run the four local checks below |
| Every pull request or `main` push | `validate-docs.yml` (Validate repository) must pass; it covers tests, notebooks, manifests, and docs |
| Monthly | Review Dependabot pull requests for `mkdocs`, `mkdocs-material`, and Actions |
| Quarterly | Re-run the local checks on a clean environment; inspect the live site |
| Before a release tag | Full strict build, link check, and a deployment verification |

## Local validation

```bash
# Once per environment
python -m venv .venv
source .venv/Scripts/activate        # Windows Git Bash; see build-and-deploy.md for PowerShell
python -m pip install -r requirements/docs.txt

# Every time
python scripts/check_docs_links.py
python -m mkdocs build --strict
python scripts/check_docs_links.py --site site
python -m mkdocs serve               # optional visual check
```

What each check covers:

| Check | Catches |
| --- | --- |
| `check_docs_links.py` | Broken relative links, missing heading anchors, nav entries that point at missing files, root-absolute links |
| `mkdocs build --strict` | Nav problems, malformed pages, duplicate/broken references, plugin warnings |
| `check_docs_links.py --site site` | Absolute URLs that lack the `/AITopics` prefix, and broken local pages or assets in the generated HTML |
| `mkdocs serve` | Rendering, search, navigation, Mermaid diagrams (visual, not automated) |

Do not commit `site/`. It is git-ignored and rebuilt in CI.

## Dependency updates

The site uses exactly two direct dependencies, declared in
`requirements/docs.txt` with compatible ranges:

```text
mkdocs>=1.6,<2
mkdocs-material>=9.6,<10
```

Update procedure:

1. Let Dependabot open the pull request, or bump the range yourself.
2. Read the release notes for breaking changes, especially theme configuration
   keys and Python version support.
3. Recreate the virtual environment and install from scratch — an incremental
   upgrade can hide a resolved dependency conflict.
4. Run all four local checks.
5. Open a page with Mermaid, tables, tabs, and admonitions; theme updates can
   change those.
6. Merge only after `validate-docs.yml` passes.

If a Material update changes rendering, pin back to the previous minor version
and open an issue rather than editing content to fit a theme bug.

### Toolchain lifecycle

Material for MkDocs reports end of life on **2027-05-05**, with critical fixes
until then. The build prints this notice on every run; it does not fail the
strict build. Keep the notice visible. Evaluate the documented successor before
that date, as described in [Build and deploy](build-and-deploy.md#toolchain-lifecycle).

## Actions maintenance

- Action versions live in `.github/workflows/deploy-pages.yml` and
  `validate-docs.yml`. Dependabot updates them monthly.
- After an action major-version bump, verify the Pages deployment still succeeds
  and that the environment URL is still reported by the deploy step.
- Do not add repository secrets for the docs build. It needs none.
- Keep `permissions` minimal: `contents: read` for builds, plus `pages: write`
  and `id-token: write` only on the deploy job.

## When the build breaks

| Failure | First command |
| --- | --- |
| Strict build error naming a file | `python -m mkdocs build --strict` |
| Link or anchor error | `python scripts/check_docs_links.py` |
| Broken styling or assets on the live site | `python scripts/check_docs_links.py --site site` |
| Deploy job failure | Read the `actions/deploy-pages` log; check Pages settings |
| Site still shows old content | Compare the deployed run's commit SHA with `main` |

Rollback: revert the offending commit on `main` and let the workflow redeploy.
Do not commit a `site/` directory as a rollback mechanism and do not force-push.

## Related documents

- [GitHub Pages publication](GITHUB-PAGES.md)
- [Build and deploy](build-and-deploy.md)
- [Troubleshooting](troubleshooting.md)
- [Maintainer guide](maintainer-guide.md)
