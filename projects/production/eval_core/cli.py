"""Shared command-line helpers for the section's labs."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field


def base_parser(description: str, *, epilog: str | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--selftest", action="store_true",
                        help="run the lab's built-in checks and exit non-zero on failure")
    parser.add_argument("--quiet", action="store_true", help="print only the result lines")
    return parser


@dataclass
class Checks:
    """A minimal check runner: no pytest, no plugins, clear output, real exit codes."""

    label: str
    results: list[tuple[str, bool, str]] = field(default_factory=list)

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        self.results.append((name, bool(condition), detail if not condition else ""))
        return bool(condition)

    def equal(self, name: str, actual, expected) -> bool:
        return self.check(name, actual == expected, f"got {actual!r}, expected {expected!r}")

    def close(self, name: str, actual: float, expected: float, tolerance: float) -> bool:
        return self.check(name, abs(actual - expected) <= tolerance,
                          f"got {actual:.6f}, expected {expected:.6f} +/- {tolerance}")

    @property
    def failed(self) -> int:
        return sum(1 for _, ok, _ in self.results if not ok)

    def report(self) -> int:
        total = len(self.results)
        passed = total - self.failed
        print(f"\n{self.label}: {passed}/{total} checks passed")
        for name, ok, detail in self.results:
            marker = "PASS" if ok else "FAIL"
            line = f"  [{marker}] {name}"
            if detail:
                line += f"  ({detail})"
            print(line)
        return 0 if self.failed == 0 else 1


def section(title: str) -> None:
    print(f"\n== {title} ==")


def fail(message: str, code: int = 2) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code
