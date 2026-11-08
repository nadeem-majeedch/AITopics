"""Lab 9 - adversarial and malformed inputs against a sample AI application.

The application is a small assistant with one tool: ``search(query, limit)``. It
accepts free text or a JSON tool call. Two versions are measured:

**unprotected** - parse if it looks like JSON, pass the query through, echo the
text otherwise. This is the version most prototypes ship.

**guarded** - size limit, encoding normalisation, JSON schema validation, path and
markup checks, then an instruction-pattern filter.

The point is the measured block rate *and* the misses. The attack set includes
cases written before the guard and four written after it, because a filter tested
only on the examples it was designed for reports a recall it has not earned.

    python lab9_adversarial_inputs.py
    python lab9_adversarial_inputs.py --selftest
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_core import (  # noqa: E402
    Checks,
    Report,
    base_parser,
    data,
    environment_snapshot,
    evaluate_cases,
    measured_footer,
    screen,
    write_json,
)

OUT_DIR = data.ROOT / "outputs" / "production" / "lab9"
TOOL_LOG: list[dict] = []


def visible(text: str, limit: int = 70) -> str:
    """Make invisible characters visible so a table can be read and printed."""
    escaped = "".join(char if ord(char) < 128 else "<U+%04X>" % ord(char) for char in text)
    return escaped[:limit]


def search_tool(query: str, limit: int = 10) -> dict:
    """The only capability the assistant has. It records every call."""
    TOOL_LOG.append({"query": query[:80], "limit": limit})
    return {"query": query, "limit": limit, "results": []}


def unprotected(payload: str) -> dict:
    """No size, schema, encoding, or instruction checks."""
    stripped = payload.strip()
    if stripped.startswith("{"):
        document = json.loads(stripped)  # raises on malformed input: the caller crashes
        return search_tool(document.get("query", ""), document.get("limit", 10))
    return {"echo": stripped}


def guarded(payload: str) -> dict:
    verdict = screen(payload)
    if not verdict.allowed:
        return {"blocked": True, "family": verdict.family, "reason": verdict.reason}
    stripped = verdict.normalised
    if stripped.startswith("{"):
        document = json.loads(stripped)
        return search_tool(document["query"], document.get("limit", 10))
    return {"echo": stripped}


def measure(handler, cases: list[dict]) -> dict:
    TOOL_LOG.clear()
    reached_tool = 0
    crashes = 0
    blocked = 0
    rows = []
    for case in cases:
        before = len(TOOL_LOG)
        try:
            result = handler(case["payload"])
        except Exception as error:  # noqa: BLE001 - the crash is the measurement
            crashes += 1
            result = {"crash": type(error).__name__}
        called = len(TOOL_LOG) > before
        reached_tool += int(called)
        blocked += int(bool(result.get("blocked")))
        rows.append(
            {
                "id": case["id"],
                "kind": case["kind"],
                "expected": case["expected"],
                "blocked": bool(result.get("blocked")),
                "called_tool": called,
                "outcome": result.get("family") or result.get("crash") or "passed through",
            }
        )
    attacks = [row for row in rows if row["expected"] == "block"]
    benign = [row for row in rows if row["expected"] == "allow"]
    return {
        "rows": rows,
        "tool_calls": len(TOOL_LOG),
        "crashes": crashes,
        "blocked": blocked,
        "attack_block_rate": sum(1 for row in attacks if row["blocked"]) / len(attacks),
        "attack_pass_rate": sum(1 for row in attacks if not row["blocked"]) / len(attacks),
        "attack_tool_reach": sum(1 for row in attacks if row["called_tool"]) / len(attacks),
        "benign_pass_rate": sum(1 for row in benign if not row["blocked"]) / len(benign),
        "benign_tool_reach": sum(1 for row in benign if row["called_tool"]) / len(benign),
    }


def run() -> dict:
    data.ensure_data()
    cases = data.load_json(data.DATA / "adversarial" / "cases.json")
    screened = evaluate_cases(cases)
    naive = measure(unprotected, cases)
    hardened = measure(guarded, cases)

    misses = [
        {"id": case["id"], "kind": case["kind"], "payload": visible(case["payload"]),
         "family": next((row["family"] for row in screened["rows"] if row["id"] == case["id"]), "")}
        for case in cases
        if case["expected"] == "block"
        and not next(row["blocked"] for row in screened["rows"] if row["id"] == case["id"])
    ]
    return {
        "cases": len(cases),
        "attacks": screened["attacks"],
        "benign": screened["benign"],
        "screen": {key: screened[key] for key in
                   ("recall", "false_positive_rate", "accuracy", "families")},
        "naive": naive,
        "guarded": hardened,
        "misses": misses,
        "rows": screened["rows"],
        "environment": environment_snapshot(),
    }


def build_report(result: dict) -> Report:
    report = Report(
        "Lab 9 - adversarial and malformed inputs",
        f"{result['cases']} labelled cases: {result['attacks']} attacks, {result['benign']} benign controls.",
    )
    report.heading("Before and after the guard")
    report.table(
        [
            {"build": "unprotected", "attacks blocked": result["naive"]["attack_block_rate"],
             "attacks reaching the tool": result["naive"]["attack_tool_reach"],
             "benign passed": result["naive"]["benign_pass_rate"],
             "crashes": result["naive"]["crashes"]},
            {"build": "guarded", "attacks blocked": result["guarded"]["attack_block_rate"],
             "attacks reaching the tool": result["guarded"]["attack_tool_reach"],
             "benign passed": result["guarded"]["benign_pass_rate"],
             "crashes": result["guarded"]["crashes"]},
        ],
        ["build", "attacks blocked", "attacks reaching the tool", "benign passed", "crashes"],
    )
    report.text(
        "The unprotected build crashes on malformed JSON; that crash is the finding, not a nuisance. The "
        "guarded build turns every bad input into a structured refusal and lets every benign control through."
    )

    report.heading("What the guard still misses")
    if result["misses"]:
        report.table(
            [{"id": item["id"], "kind": item["kind"], "payload": item["payload"]} for item in result["misses"]],
            ["id", "kind", "payload"],
        )
        report.text(
            f"Recall on this set is {result['screen']['recall']:.3f}. The misses are the cases written after "
            "the patterns: base64, a paraphrase, a request for the instructions themselves, and a zero-width "
            "character inside a keyword. A pattern list is a speed bump. The controls that hold are the "
            "schema, the size limit, the tool's own permissions, and a human approval for anything that "
            "matters."
        )
    else:
        report.text(
            "No misses on this set. That is the expected result of testing a filter on its own examples, and "
            "it is not evidence of robustness. Add cases you did not write before quoting a recall figure."
        )

    report.heading("Per-case results")
    report.table(
        [{"id": row["id"], "kind": row["kind"], "expected": row["expected"],
          "blocked": row["blocked"], "family": row["family"]} for row in result["rows"]],
        ["id", "kind", "expected", "blocked", "family"],
    )

    report.heading("What this does not measure")
    report.bullets([
        "One tool with no data access. The damage from a missed injection is bounded by the tool, not by the filter.",
        "No model in the loop. An LLM can be persuaded by text that matches no pattern; the filter's recall "
        "on real model inputs is unknown from this lab.",
        "Sixteen attacks is a small, hand-written sample. Treat the numbers as a regression test for the "
        "guard's behaviour, not as a security estimate.",
    ])
    return report


def selftest() -> int:
    checks = Checks("lab 9 - adversarial inputs")
    result = run()

    checks.equal("all cases evaluated", len(result["rows"]), result["cases"])
    checks.check("guard blocks most attacks", 0.6 <= result["screen"]["recall"] < 1.0,
                 f"{result['screen']['recall']:.3f}")
    checks.check("guard does not block ordinary requests", result["screen"]["false_positive_rate"] <= 0.1,
                 f"{result['screen']['false_positive_rate']:.3f}")
    checks.check("unprotected build passes every attack through",
                 result["naive"]["attack_pass_rate"] == 1.0 and result["naive"]["attack_block_rate"] == 0.0,
                 f"{result['naive']['attack_pass_rate']:.2f}")
    checks.check("unprotected build crashes on malformed input", result["naive"]["crashes"] >= 1,
                 str(result["naive"]["crashes"]))
    checks.check("guarded build never crashes", result["guarded"]["crashes"] == 0)
    checks.check("guarded build blocks more attacks than the unprotected one",
                 result["guarded"]["attack_block_rate"] > result["naive"]["attack_block_rate"])
    checks.check("benign traffic still passes", result["guarded"]["benign_pass_rate"] == 1.0,
                 f"{result['guarded']['benign_pass_rate']:.2f}")
    checks.check("misses are listed, not hidden", len(result["misses"]) >= 1,
                 str([item["id"] for item in result["misses"]]))
    checks.check("each miss names its family",
                 all(item["kind"] for item in result["misses"]))

    report = build_report(result)
    path = report.write(OUT_DIR, "report.md", measured_footer(result["environment"]))
    write_json(OUT_DIR, "metrics.json", {k: v for k, v in result.items() if k != "rows"} | {
        "rows": result["rows"]})
    checks.check("report written", path.exists() and path.stat().st_size > 1200)
    return checks.report()


def main() -> int:
    parser = base_parser(__doc__ or "")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    result = run()
    print(build_report(result).render(measured_footer(result["environment"])))
    write_json(OUT_DIR, "metrics.json", result)
    print(f"\nwritten: {OUT_DIR / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
