"""Safe model artifacts: digests, schemas, and why pickle is a code-execution risk.

An artifact is not just data. A ``.pkl`` file is a program: unpickling calls
``__reduce__``, and ``__reduce__`` can name any callable. That is not a bug in
pickle; it is what pickle is for. The consequence is that "load the model file"
and "run untrusted code" are the same operation.

This module provides the pattern the lesson recommends:

* prefer weights-only, non-executable formats (``.npz`` with ``allow_pickle=False``,
  ``safetensors``, ONNX);
* record a SHA-256 digest and verify it before loading;
* if pickle is unavoidable, load through an allowlist that permits only known
  classes.

``make_teaching_payload`` builds a benign demonstration object whose unpickling
prints a line. It grants no access and touches no files; the point is that the
print happens at all.
"""

from __future__ import annotations

import hashlib
import io
import json
import pickle
from pathlib import Path

import numpy as np

ALLOWED_GLOBALS = {
    ("json", "loads"),
    ("collections", "OrderedDict"),
    ("numpy.core.multiarray", "_reconstruct"),
    ("numpy", "ndarray"),
    ("numpy", "dtype"),
}


class RestrictedUnpickler(pickle.Unpickler):
    """An unpickler that refuses every global not on the allowlist."""

    def find_class(self, module: str, name: str):  # noqa: D102 - documented above
        if (module, name) not in ALLOWED_GLOBALS:
            raise pickle.UnpicklingError(f"blocked global: {module}.{name}")
        return super().find_class(module, name)


def restricted_loads(payload: bytes):
    return RestrictedUnpickler(io.BytesIO(payload)).load()


class TeachingPayload:
    """Unpickling this calls ``print``. That is the whole demonstration."""

    def __init__(self, message: str = "payload executed during unpickling"):
        self.message = message

    def __reduce__(self):
        return (print, (self.message,))


def make_teaching_payload(message: str = "payload executed during unpickling") -> bytes:
    return pickle.dumps(TeachingPayload(message))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def save_weights(path: Path, params: dict[str, np.ndarray]) -> str:
    """Save weights without pickle, and return the digest of the bytes on disk."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **{name: np.asarray(value) for name, value in params.items()})
    return sha256_bytes(path.read_bytes())


def load_weights(path: Path, expected_sha256: str | None = None) -> dict[str, np.ndarray]:
    """Load ``.npz`` weights, refusing a digest mismatch before reading arrays."""
    path = Path(path)
    digest = sha256_bytes(path.read_bytes())
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"artifact digest mismatch: {digest} != {expected_sha256}")
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name] for name in archive.files}


def write_manifest(path: Path, artifacts: dict[str, Path], metadata: dict | None = None) -> Path:
    path = Path(path)
    manifest = {
        "files": {
            name: {"sha256": sha256_bytes(artifact.read_bytes()), "bytes": artifact.stat().st_size}
            for name, artifact in artifacts.items()
        },
        "metadata": metadata or {},
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def verify_manifest(manifest_path: Path) -> list[str]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    base = Path(manifest_path).parent
    problems = []
    for name, record in manifest["files"].items():
        target = base / name
        if not target.exists():
            problems.append(f"missing: {name}")
            continue
        if sha256_bytes(target.read_bytes()) != record["sha256"]:
            problems.append(f"digest mismatch: {name}")
    return problems
