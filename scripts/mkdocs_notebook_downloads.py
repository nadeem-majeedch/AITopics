# SPDX-License-Identifier: MIT
"""Add a visible download link to every rendered notebook page.

``mkdocs-jupyter`` copies each notebook to the site beside its rendered page
(``notebooks/<area>/<stem>/<stem>.ipynb``) when ``include_source`` is enabled,
but it does not link to that copy. This hook prepends a download button so
students can fetch the original ``.ipynb`` without constructing a URL.

Declared in ``mkdocs.yml`` under ``hooks:``. No extra dependency is required:
MkDocs runs hooks itself.
"""

from __future__ import annotations

from typing import Any

# The downloaded file sits in the same directory as the rendered page, so a bare
# filename resolves correctly on any hosting path, including /AITopics/.
# The visible text is the accessible name: no aria-label overrides it, so speech
# input and screen readers use the same words (WCAG 2.5.3, Label in Name).
BANNER = (
    '<div class="notebook-download" style="margin: 1rem 0 1.5rem;">'
    '<a class="md-button md-button--primary" href="{name}" download>'
    "Download notebook (.ipynb)"
    "</a>"
    "</div>"
)


def on_page_content(
    html: str,
    page: Any,
    config: Any,
    files: Any,
) -> str:
    """Prepend the download button when the source page is a notebook."""

    # src_uri is always POSIX-style; src_path uses the host separator.
    src_uri = str(page.file.src_uri)
    if not src_uri.lower().endswith(".ipynb"):
        return html
    name = src_uri.rsplit("/", 1)[-1]
    return BANNER.format(name=name) + html
