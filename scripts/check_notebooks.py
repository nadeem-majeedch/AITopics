"""Validate notebook JSON, or execute the course notebooks on a CPU kernel.

Run from the repository root:

    python scripts/check_notebooks.py --validate
    python scripts/check_notebooks.py --execute
    python scripts/check_notebooks.py --execute --timeout 300

``--validate`` parses every ``.ipynb`` under ``notebooks/`` with ``nbformat``,
checks the notebook schema, rejects stored error outputs, and requires every code
cell to have an execution count. The course claims its notebooks were executed
top-to-bottom, so an unexecuted or failed cell is a release defect.

``--execute`` also runs each notebook with a fresh kernel in its own directory and
fails on the first uncaught cell error. Nothing is written back to the notebook.
Every notebook is offline and CPU-compatible: no model weights, API keys, or GPU
are required. The optional GPU and Hugging Face branches are guarded by the
notebooks themselves, so execution here is only the mandatory CPU path.

Exit status is 0 when clean and 1 when a notebook is invalid or fails to execute.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def discover() -> list[Path]:
    paths = sorted(NOTEBOOKS.rglob("*.ipynb"))
    if not paths:
        raise FileNotFoundError(f"no notebooks found under {NOTEBOOKS}")
    return paths


def validate_notebook(path: Path) -> list[str]:
    """Return structural problems in one notebook; never execute it."""
    problems: list[str] = []
    try:
        notebook = nbformat.read(path, as_version=4)
    except Exception as exc:  # nbformat raises several unrelated types
        return [f"{path.relative_to(ROOT)}: cannot parse: {type(exc).__name__}: {exc}"]

    try:
        nbformat.validate(notebook)
    except Exception as exc:
        problems.append(f"{path.relative_to(ROOT)}: invalid notebook schema: {exc}")

    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    if not code_cells:
        problems.append(f"{path.relative_to(ROOT)}: no code cells")

    for index, cell in enumerate(notebook.cells, start=1):
        if cell.cell_type != "code":
            continue
        if cell.get("execution_count") is None:
            problems.append(f"{path.relative_to(ROOT)}: cell {index} has no execution count")
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                ename = output.get("ename", "Error")
                problems.append(f"{path.relative_to(ROOT)}: cell {index} stores {ename} output")
    return problems


def execute_notebook(path: Path, timeout: int) -> tuple[int, float]:
    """Execute one notebook in memory and return (code cell count, seconds)."""
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name="python3",
        allow_errors=False,
        resources={"metadata": {"path": str(path.parent)}},
    )
    started = time.monotonic()
    client.execute()
    elapsed = time.monotonic() - started
    code_cells = sum(1 for cell in notebook.cells if cell.cell_type == "code")
    return code_cells, elapsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--validate", action="store_true", help="validate JSON and stored outputs only")
    mode.add_argument("--execute", action="store_true", help="validate and execute every notebook")
    parser.add_argument("--timeout", type=int, default=300, help="per-cell timeout in seconds")
    args = parser.parse_args(argv)

    # Keep execution headless and offline. The notebooks do not download models or
    # data; these settings turn an accidental network path into a clear failure.
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    paths = discover()
    problems: list[str] = []
    for path in paths:
        problems.extend(validate_notebook(path))

    if problems:
        print(f"{len(problems)} notebook problem(s) in {len(paths)} notebook(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"ok: {len(paths)} notebooks are valid JSON, executed, and free of stored errors")

    if not args.execute:
        return 0

    print(f"executing {len(paths)} notebooks with a {args.timeout}s per-cell timeout")
    executed_cells = 0
    started = time.monotonic()
    for path in paths:
        try:
            cells, elapsed = execute_notebook(path, args.timeout)
        except CellExecutionError as exc:
            print(f"FAIL {path.relative_to(ROOT)}")
            print(str(exc))
            return 1
        except Exception as exc:
            print(f"FAIL {path.relative_to(ROOT)}: {type(exc).__name__}: {exc}")
            return 1
        executed_cells += cells
        print(f"  ok {elapsed:5.1f}s  {cells:2d} cells  {path.relative_to(ROOT)}")

    total = time.monotonic() - started
    print(f"ok: executed {len(paths)} notebooks, {executed_cells} code cells in {total:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
