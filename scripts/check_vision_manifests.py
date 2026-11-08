"""Verify present computer-vision datasets, with explicit PASS/FAIL/SKIPPED.

Run from the repository root:

    python scripts/check_vision_manifests.py
    python scripts/check_vision_manifests.py --require-datasets
    python scripts/check_vision_manifests.py --data-dir tests/tmp/fixture

``data/`` is git-ignored because the synthetic datasets are generated, so a fresh
checkout normally has no images. That is reported as **SKIPPED**, never as a
successful integrity check. Exit status is 0 for an optional skip, 1 for a real
integrity failure, and 2 when ``--require-datasets`` was passed and no dataset
was found.

When a dataset directory exists, its ``manifest.json`` is checked with the same
rules as ``scripts/make_vision_data.py --check``: missing, modified, unexpected,
or cross-split duplicate files; invalid labels; class presence in every split;
and source-group overlap.

Byte-identical variants inside one split are reported as warnings, not failures.
The original P06 set has 57 documented same-split warnings; they are redundant
copies, not leakage, and the controlled deduplication study found no benefit from
removing them. Datasets are never regenerated here.

``--data-dir`` exists so CI and tests can run this script against a tiny synthetic
fixture without downloading or generating the complete P06 corpus. Use
``--require-datasets`` only in the optional real-data job, where a missing
dataset should fail rather than skip.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computer-vision"
sys.path.insert(0, str(ROOT / "projects" / "computer-vision"))

from vision_core import manifest  # noqa: E402


def dataset_directories(data: Path) -> list[Path]:
    """Manifest-managed P06 directories; a missing manifest is a failure."""
    if not data.is_dir():
        return []
    return sorted(path for path in data.glob("objects_p06*") if path.is_dir())


def run(data: Path, require_datasets: bool) -> int:
    directories = dataset_directories(data)
    if not directories:
        print(
            "SKIPPED: no generated datasets under "
            f"{data} (data/ is git-ignored; nothing was regenerated)"
        )
        if require_datasets:
            print("RESULT: SKIPPED (datasets required by --require-datasets)")
            return 2
        print("RESULT: SKIPPED (optional; pass --require-datasets to make this a failure)")
        return 0

    failures = 0
    warned = 0
    for directory in directories:
        result = manifest.check_dataset(directory)
        status = "PASS" if result["ok"] else "FAIL"
        print(f"{status}: {directory.name}")
        print("\n".join(manifest.summarize(result)))
        warnings = len(result.get("warnings", []))
        warned += warnings
        if not result["ok"]:
            failures += 1

    if failures:
        print(
            f"\nRESULT: FAIL - {len(directories)} dataset(s), "
            f"{failures} failed, {warned} duplicate-content warning(s)"
        )
        return 1

    print(
        f"\nRESULT: PASS - {len(directories)} dataset(s), 0 failed, "
        f"{warned} duplicate-content warning(s) accepted"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA,
        help="directory containing objects_p06* datasets (default: data/computer-vision)",
    )
    parser.add_argument(
        "--require-datasets",
        action="store_true",
        help="return status 2 when no dataset is present instead of an optional skip",
    )
    args = parser.parse_args(argv)
    return run(args.data_dir, args.require_datasets)


if __name__ == "__main__":
    raise SystemExit(main())
