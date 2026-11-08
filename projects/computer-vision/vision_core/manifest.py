"""Dataset manifests and integrity checks for generated image sets.

The P06 object set is generated deterministically, but a file can still be
deleted, overwritten, or moved between runs, and a split can silently lose a
class. This module writes a JSON manifest with a SHA-256 digest, size, label and
source group for every image, then verifies an existing directory against it.
Byte-identical files within one split are reported as warnings (redundant data);
the same bytes across splits are failures (leakage).

The manifest contains no timestamps or absolute paths, so regenerating the same
seed produces the same file. ``check_dataset`` returns a machine-readable report;
``scripts/make_vision_data.py --check`` prints a human-readable summary and writes
the report to ``manifest_check.json``.

Exit-style usage::

    from vision_core import manifest
    manifest.write_manifest(root, manifest.build_manifest(root, splits, classes, ...))
    result = manifest.check_dataset(root)
    print("\\n".join(manifest.summarize(result)))
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Sequence

MANIFEST_NAME = "manifest.json"
CHECK_NAME = "manifest_check.json"
VERSION = "1.0.0"


def sha256(path: Path) -> str:
    """Hash a file in chunks so large images do not need to be loaded whole."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    root: str | Path,
    splits: dict[str, Sequence[Any]],
    classes: Sequence[str],
    *,
    dataset: str,
    version: str = VERSION,
    seed: int | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe every ``<split>/<index>.png`` image under ``root``.

    ``splits`` is the in-memory split returned by the generator, so the manifest
    records the intended label and source group next to the file digest. A file
    missing at this point is a generation bug and raises immediately.
    """
    root = Path(root)
    files: dict[str, dict[str, Any]] = {}
    split_names = sorted(splits)
    for split in split_names:
        for index, record in enumerate(splits[split]):
            relative = f"{split}/{index:05d}.png"
            path = root / relative
            if not path.exists():
                raise FileNotFoundError(f"cannot manifest missing image: {path}")
            label = int(record.label)
            files[relative] = {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "split": split,
                "label": label,
                "label_name": classes[label] if 0 <= label < len(classes) else str(label),
                "source_id": str(record.source_id),
            }

    class_counts = {split: {name: 0 for name in classes} for split in split_names}
    source_groups = {split: set() for split in split_names}
    for entry in files.values():
        split = entry["split"]
        label = entry["label"]
        source_groups[split].add(entry["source_id"])
        if 0 <= label < len(classes):
            class_counts[split][classes[label]] += 1

    return {
        "dataset": dataset,
        "version": version,
        "classes": list(classes),
        "seed": seed,
        "parameters": parameters or {},
        "splits": {split: sum(1 for e in files.values() if e["split"] == split) for split in split_names},
        "class_counts": class_counts,
        "source_groups": {split: len(groups) for split, groups in source_groups.items()},
        "files": files,
    }


def write_manifest(root: str | Path, payload: dict[str, Any]) -> Path:
    """Write ``manifest.json`` in a stable key order and line ending."""
    path = Path(root) / MANIFEST_NAME
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _problem(result: dict[str, Any], code: str, path: str, detail: str) -> None:
    result["problems"].append({"code": code, "path": path, "detail": detail})


def _warning(result: dict[str, Any], code: str, path: str, detail: str) -> None:
    result["warnings"].append({"code": code, "path": path, "detail": detail})


def check_dataset(
    root: str | Path,
    classes: Sequence[str] | None = None,
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    """Verify a generated image directory against its manifest.

    Checks missing, modified, unexpected and byte-identical files; label and
    label-name agreement; class presence in every split; source-group label
    consistency; and source overlap between splits. Returns ``ok`` plus a list of
    problems, each with a stable ``code`` for tests and scripts.
    """
    root = Path(root)
    manifest_path = Path(manifest_path) if manifest_path else root / MANIFEST_NAME
    result: dict[str, Any] = {
        "ok": False,
        "dataset": root.name,
        "version": None,
        "manifest": str(manifest_path),
        "checked_files": 0,
        "problems": [],
        "warnings": [],
        "class_counts": {},
        "source_groups": {},
        "source_overlap": {},
        "declared_splits": {},
    }

    if not manifest_path.exists():
        _problem(result, "manifest_missing", str(manifest_path), f"run the generator to create {MANIFEST_NAME}")
        return result

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        files: dict[str, dict[str, Any]] = payload["files"]
        declared_splits: dict[str, int] = payload["splits"]
        manifest_classes = list(payload.get("classes", []))
    except (KeyError, TypeError, ValueError) as exc:
        _problem(result, "manifest_invalid", str(manifest_path), f"{type(exc).__name__}: {exc}")
        return result

    result["dataset"] = payload.get("dataset")
    result["version"] = payload.get("version")
    result["declared_splits"] = declared_splits
    names = list(classes) if classes is not None else manifest_classes
    result["classes"] = names

    # ----- per-file checks -------------------------------------------------
    per_split: dict[str, Counter] = defaultdict(Counter)
    source_labels: dict[str, set[int]] = defaultdict(set)
    source_splits: dict[str, set[str]] = defaultdict(set)
    by_hash: dict[str, list[str]] = defaultdict(list)

    for relative, entry in sorted(files.items()):
        path = root / relative
        result["checked_files"] += 1
        parent = relative.split("/")[0] if "/" in relative else ""

        if not path.is_file():
            _problem(result, "missing_file", relative, "listed in the manifest but absent on disk")
        else:
            if path.stat().st_size != entry.get("bytes"):
                _problem(result, "modified_file", relative, "size differs from the manifest")
            elif sha256(path) != entry.get("sha256"):
                _problem(result, "modified_file", relative, "sha256 differs from the manifest")

        label = entry.get("label")
        split = entry.get("split", parent)
        if not isinstance(label, int) or not 0 <= label < len(names):
            _problem(result, "bad_label", relative, f"label {label!r} is outside 0..{len(names) - 1}")
        elif entry.get("label_name") != names[label]:
            _problem(
                result,
                "bad_label",
                relative,
                f"label_name {entry.get('label_name')!r} does not match classes[{label}] {names[label]!r}",
            )
        else:
            per_split[split][names[label]] += 1

        if split != parent:
            _problem(result, "split_mismatch", relative, f"metadata says {split!r}, path says {parent!r}")

        source = entry.get("source_id")
        if not isinstance(source, str) or not source:
            _problem(result, "bad_source_id", relative, f"invalid source_id {source!r}")
        else:
            if isinstance(label, int):
                source_labels[source].add(label)
            source_splits[source].add(split)

        digest = entry.get("sha256")
        if isinstance(digest, str):
            by_hash[digest].append(relative)

    # ----- duplicate content ----------------------------------------------
    # Identical bytes within one split are redundant data, not corruption: two
    # synthetic sources can legitimately render the same picture. Identical
    # bytes across splits are a leakage failure, because the test image is also
    # a train image no matter which source labels claim otherwise.
    for digest, paths in sorted(by_hash.items()):
        if len(paths) < 2:
            continue
        parts = {files[relative].get("split") for relative in paths}
        detail = "identical bytes at: " + ", ".join(paths)
        if len(parts) > 1:
            _problem(result, "duplicate_across_splits", paths[0], detail)
        else:
            _warning(result, "duplicate_content", paths[0], detail)

    # ----- source-group integrity -----------------------------------------
    for source, labels in sorted(source_labels.items()):
        if len(labels) > 1:
            names_for_source = ", ".join(names[i] if i < len(names) else str(i) for i in sorted(labels))
            _problem(result, "source_label_conflict", source, f"one source group has multiple labels: {names_for_source}")
    for source, parts in sorted(source_splits.items()):
        if len(parts) > 1:
            _problem(result, "split_overlap", source, "source group appears in: " + ", ".join(sorted(parts)))
            result["source_overlap"][source] = sorted(parts)

    # ----- class presence and declared counts -----------------------------
    split_names = sorted(set(declared_splits) | set(per_split))
    result["class_counts"] = {split: {name: 0 for name in names} for split in split_names}
    for split in split_names:
        for name in names:
            result["class_counts"][split][name] = per_split[split][name]
        for name in names:
            if per_split[split][name] == 0:
                _problem(result, "class_missing", split, f"class {name!r} has no images in this split")
        actual = sum(per_split[split].values())
        declared = declared_splits.get(split)
        if declared is not None and declared != actual:
            _problem(
                result,
                "split_count_mismatch",
                split,
                f"manifest declares {declared} images, found {actual}",
            )
        source_count = len({s for s, parts in source_splits.items() if split in parts})
        result["source_groups"][split] = source_count

    # ----- unexpected files ------------------------------------------------
    allowed_root_sidecars = {MANIFEST_NAME, CHECK_NAME}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in files:
            continue
        if path.parent == root and (path.name in allowed_root_sidecars or path.suffix in {".csv", ".npy"}):
            continue
        _problem(result, "unexpected_file", relative, "not listed in the manifest")

    result["ok"] = not result["problems"]
    return result


def summarize(result: dict[str, Any], limit: int = 20) -> list[str]:
    """Human-readable lines for a check report; never invents a pass."""
    warning_count = len(result.get("warnings", []))
    if result["ok"]:
        lines = [
            f"{result['dataset']} manifest v{result['version']}: OK"
            + (f" ({warning_count} warning(s))" if warning_count else ""),
            f"  {result['checked_files']} images checked against {MANIFEST_NAME}",
        ]
    else:
        lines = [
            f"{result['dataset']} manifest v{result['version']}: FAIL",
            f"  {result['checked_files']} images checked, {len(result['problems'])} problem(s)",
        ]

    if result.get("class_counts"):
        lines.append("  per split (images / sources):")
        for split, counts in result["class_counts"].items():
            total = sum(counts.values())
            groups = result.get("source_groups", {}).get(split, "?")
            per_class = ", ".join(f"{name} {count}" for name, count in counts.items())
            lines.append(f"    {split}: {total} images / {groups} sources ({per_class})")

    if result.get("source_overlap"):
        lines.append(f"  leaked source groups: {len(result['source_overlap'])}")
    elif result["ok"]:
        lines.append("  source overlap: none")

    for warning in result.get("warnings", [])[: min(limit, 5)]:
        lines.append(f"  warning [{warning['code']}] {warning['path']}: {warning['detail']}")

    for problem in result["problems"][:limit]:
        lines.append(f"  [{problem['code']}] {problem['path']}: {problem['detail']}")
    if len(result["problems"]) > limit:
        lines.append(f"  ... {len(result['problems']) - limit} more problem(s) in {CHECK_NAME}")
    return lines
