# Navigation and link audit

Audit date: **2026-11-08**. Scope: MkDocs navigation, Markdown links and
anchors, built HTML links, `/AITopics/` URL handling, and direct notebook access.

## Verdict

**PASS.** Every notebook is reachable from the navigation and from the Notebook
Library. The strict build completes without warnings, and the built-site checker
finds no broken relative links or root-absolute URLs that would bypass the
project-site prefix.

## Navigation structure

The site navigation now includes:

- a **Notebook Library** page with direct links to all 26 notebooks;
- a **Notebook Library** navigation section listing all 26 notebooks;
- direct notebook links from the lessons index and each section index;
- direct notebook links from every foundation notebook guide;
- lesson, lab, assessment, project, capstone, and technical sections.

The six applied notebooks are mounted by `mkdocs-jupyter` with:

```yaml
notebook_dirs: notebooks: notebooks
include_source: true
```

This keeps the repository's `notebooks/` directory as the single source of truth
instead of copying notebooks into `docs/`.

## Verification commands

```bash
python scripts/check_docs_links.py
python -m mkdocs build --strict -d site
python scripts/check_docs_links.py --site site
```

## Results

| Check | Result |
| --- | --- |
| Source Markdown files, links, anchors, and nav entries | **PASS: 295 Markdown files, 0 broken links** |
| Strict MkDocs build | **PASS: 0 warnings** |
| Built pages | **322 pages** |
| Built-site relative links and assets | **PASS** |
| Absolute URLs under `/AITopics/` | **PASS** |
| Notebooks listed in navigation | **26 of 26** |
| Notebooks linked from Notebook Library | **26 of 26** |

## Fixes made in this pass

- Added all 26 notebooks to `mkdocs.yml` and to
  `docs/notebook-library.md`.
- Updated section indexes and foundation notebook guides with direct notebook
  links at the correct relative depth.
- Fixed M15/M16 previous/next links after the notebook pages were mounted one
  directory deeper than the source notebooks.
- Taught the link checker to resolve virtual `mkdocs-jupyter` notebook paths and
  navigation entries.
- Removed trailing whitespace from the new documentation links; both
  `git diff --check` and `git diff --cached --check` are clean.
- Removed all empty notebook placeholder directories.

## Remaining navigation limitations

- The public GitHub Pages site is still absent (HTTP 404), so the built site has
  been checked locally and in the built output, not on the public origin.
- The built-site checker validates links, assets, and prefix handling; it is not
  a browser interaction test.
- Search quality and mobile rendering were not evaluated by a human student.

For the publication status, see the
[GitHub Pages deployment audit](github-pages-deployment-audit.md).
