"""Shared command-line helpers so every project behaves the same way.

Standard flags:

``--selftest``       run the built-in checks and exit non-zero on failure
``--local``          optional local ``transformers`` model
``--hosted``         optional OpenAI-compatible endpoint (needs AGENT_* env vars)
``--allow-network``  explicit consent to send data to that endpoint
``--trace-dir``      where JSONL traces are written

The default is always offline and deterministic, because a course exercise that
needs a credit card is not an exercise.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .model import HostedChatModel, LocalTransformersModel, Model


def base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--selftest", action="store_true", help="run built-in checks and exit")
    parser.add_argument("--local", action="store_true", help="use an optional local transformers model")
    parser.add_argument("--hosted", action="store_true", help="use an optional hosted chat endpoint")
    parser.add_argument("--allow-network", action="store_true",
                        help="explicitly allow network calls (required with --hosted)")
    parser.add_argument("--trace-dir", type=Path, default=None, help="directory for JSONL traces")
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    return parser


def choose_model(args: argparse.Namespace, *, local_name: str = "HuggingFaceTB/SmolLM2-360M-Instruct") -> Model | None:
    """Return an optional real model, or None to stay on the scripted path."""

    if getattr(args, "hosted", False):
        model = HostedChatModel.from_env(allow_network=bool(getattr(args, "allow_network", False)))
        if model is None:
            print(
                "No hosted endpoint configured. Set AGENT_BASE_URL, AGENT_MODEL, and "
                "AGENT_API_KEY in your environment, or run without --hosted.",
                file=sys.stderr,
            )
            return None
        if not model.allow_network:
            print("--hosted also needs --allow-network, because it sends your data out.",
                  file=sys.stderr)
            return None
        return model

    if getattr(args, "local", False):
        if not LocalTransformersModel.available():
            print("transformers is not installed; staying offline. See requirements/agents.txt.",
                  file=sys.stderr)
            return None
        return LocalTransformersModel(model_name=local_name)
    return None


class Checks:
    """Tiny assertion collector so a demo can report every check, not just the first."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.results: list[tuple[bool, str, str]] = []

    def check(self, label: str, condition: bool, detail: str = "") -> bool:
        self.results.append((bool(condition), label, detail))
        return bool(condition)

    def equal(self, label: str, got, expected) -> bool:
        return self.check(label, got == expected, f"got {got!r}, expected {expected!r}")

    def report(self) -> int:
        passed = sum(1 for ok, _, _ in self.results if ok)
        total = len(self.results)
        print(f"\n{self.title}: {passed}/{total} checks passed")
        for ok, label, detail in self.results:
            mark = "PASS" if ok else "FAIL"
            suffix = f"  ({detail})" if detail and not ok else ""
            print(f"  [{mark}] {label}{suffix}")
        return 0 if passed == total else 1


def write_json(path: Path, payload) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default
