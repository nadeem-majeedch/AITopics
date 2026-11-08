"""Loading and describing the section's data.

The section never ships data in git. ``scripts/make_eval_data.py`` generates it
from a fixed seed, and this module loads it in one place so that every lab reads
the same bytes and can prove it with a digest.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "production"
GENERATOR = ROOT / "scripts" / "make_eval_data.py"


def ensure_data() -> Path:
    """Generate the data if it is missing. Idempotent and offline."""
    if not (DATA / "manifest.json").exists():
        subprocess.run([sys.executable, str(GENERATOR)], check=True, capture_output=True)
    return DATA


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict]:
    """Read a CSV into typed rows: ints, floats, and strings, in that order."""
    rows: list[dict] = []
    with open(path, newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            row: dict = {}
            for key, value in raw.items():
                row[key] = _coerce(value)
            rows.append(row)
    return rows


def _coerce(value: str):
    if value == "":
        return ""
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def feature_matrix(rows: list[dict], numeric: list[str], categorical: list[str],
                   reference: dict[str, list[str]] | None = None):
    """Build a float matrix, one-hot encoding categories against fixed levels.

    ``reference`` keeps the encoding identical between train and test rows. Passing
    a fitted encoding is what stops a category that appears only in the test set
    from silently becoming a different column.
    """
    levels = {column: sorted({str(row[column]) for row in rows}) for column in categorical}
    if reference is not None:
        levels = reference
    names = list(numeric)
    for column in categorical:
        names.extend(f"{column}={level}" for level in levels[column])

    matrix = []
    for row in rows:
        vector = [float(row[column]) for column in numeric]
        for column in categorical:
            vector.extend(1.0 if str(row[column]) == level else 0.0 for level in levels[column])
        matrix.append(vector)
    return matrix, names, levels


def target(rows: list[dict], column: str = "churned") -> list[int]:
    return [int(row[column]) for row in rows]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest_status(data_dir: Path | None = None) -> dict:
    """Compare on-disk files with the generator's manifest."""
    data_dir = Path(data_dir or DATA)
    manifest = load_json(data_dir / "manifest.json")
    mismatched = [
        name for name, record in manifest["files"].items()
        if not (data_dir / name).exists() or sha256_file(data_dir / name) != record["sha256"]
    ]
    return {
        "seed": manifest["seed"],
        "files": len(manifest["files"]),
        "bytes": sum(record["bytes"] for record in manifest["files"].values()),
        "mismatched": mismatched,
    }


def environment_snapshot() -> dict:
    """The minimum environment record needed to reproduce a measurement."""
    versions = {"python": sys.version.split()[0], "platform": platform.platform()}
    for module in ("numpy", "sklearn", "pandas"):
        try:
            versions[module] = __import__(module).__version__
        except Exception:  # pragma: no cover - only when a package is absent
            versions[module] = "not installed"
    versions["machine"] = platform.machine()
    versions["byteorder"] = sysconfig.get_config_var("BYTEORDER") or "unknown"
    return versions
