"""Project D - a data-analysis agent that reads a CSV and writes a report.

Architecture
------------
::

    workspace/                     one sandbox root, nothing else is reachable
      sales.csv                    copied in before the run
      reports/summary.md           the only place the agent may write

    profile_csv  ->  columns, row count, per-column problems, duplicate rows
    summarize    ->  totals, per-region revenue, return rate, growth
    write_report ->  markdown file, requires human approval, size-limited

The analysis is plain Python over ``csv``: no pandas, no sampling, no hidden
state. Every number in the report can be reproduced by hand, which is the point
of a report an agent produces.

Data quality is part of the output. The messy fixture has a missing revenue, a
negative quantity, and a padded number; the agent flags all three instead of
crashing or silently dropping rows. A report that hides its own defects is worse
than no report.

Run
---
    python project_d_csv_analyst.py --selftest
    python project_d_csv_analyst.py                      # clean fixture
    python project_d_csv_analyst.py --file sales_messy.csv --deny-write

Limitations
-----------
The aggregation is fixed: revenue by region, units, return rate, quarter-over-
quarter change. A general analyst would need SQL or a code tool; both widen the
attack surface, which is why this project deliberately has neither.
"""

from __future__ import annotations

import argparse
import csv
import io
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_core import (  # noqa: E402
    Policy,
    RunLimits,
    SandboxFS,
    ScriptedApprover,
    ScriptedModel,
    ToolRegistry,
    ToolSpec,
    object_schema,
    run_agent,
)
from agent_core.cli import Checks, base_parser  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data" / "agents" / "csv"
OUT_DIR = REPO_ROOT / "outputs" / "agents" / "project_d"

REQUIRED_COLUMNS = ("quarter", "region", "units", "unit_price", "revenue", "returns")

PROFILE_INPUT = object_schema({"path": {"type": "string", "minLength": 1, "maxLength": 200}})
SUMMARY_INPUT = object_schema(
    {
        "path": {"type": "string", "minLength": 1, "maxLength": 200},
        "group_by": {"type": "string", "enum": ["region", "quarter"]},
    },
    required=["path"],
)
WRITE_INPUT = object_schema(
    {
        "path": {"type": "string", "minLength": 1, "maxLength": 200},
        "markdown": {"type": "string", "minLength": 20, "maxLength": 12000},
    }
)


def _number(raw: str) -> tuple[float | None, str | None]:
    text = (raw or "").strip()
    if text == "":
        return None, "missing"
    try:
        return float(text), None
    except ValueError:
        return None, f"not a number ({raw!r})"


def load_rows(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse and validate. Returns usable rows plus a list of problems."""

    issues: list[str] = []
    reader = csv.DictReader(io.StringIO(text))
    header = reader.fieldnames or []
    missing = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing:
        raise ValueError(f"missing columns: {', '.join(missing)}")

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for line_number, raw in enumerate(reader, start=2):
        quarter = (raw.get("quarter") or "").strip()
        region = (raw.get("region") or "").strip().lower()
        units, units_problem = _number(raw.get("units", ""))
        price, price_problem = _number(raw.get("unit_price", ""))
        revenue, revenue_problem = _number(raw.get("revenue", ""))
        returns, returns_problem = _number(raw.get("returns", ""))

        if not quarter or not region:
            issues.append(f"line {line_number}: missing quarter or region; row skipped")
            continue
        for problem in (units_problem, price_problem, returns_problem):
            if problem:
                issues.append(f"line {line_number}: {problem} in units/price/returns; row skipped")
                break
        else:
            if units is not None and units < 0:
                issues.append(f"line {line_number}: negative units ({units:g}); row excluded")
                continue
            if revenue_problem:
                issues.append(
                    f"line {line_number}: revenue {revenue_problem}; recomputed from units x price"
                )
                revenue = units * price if units is not None and price is not None else None
            if revenue is None:
                issues.append(f"line {line_number}: revenue unavailable; row excluded")
                continue
            key = (quarter, region)
            if key in seen:
                issues.append(f"line {line_number}: duplicate {quarter}/{region}; row excluded")
                continue
            seen.add(key)
            rows.append(
                {
                    "quarter": quarter,
                    "region": region,
                    "units": float(units or 0),
                    "unit_price": float(price or 0),
                    "revenue": float(revenue),
                    "returns": float(returns or 0),
                }
            )
    return rows, issues


def summarize(rows: list[dict[str, Any]], group_by: str = "region") -> dict[str, Any]:
    if not rows:
        return {"rows": 0, "total_revenue": 0.0, "total_units": 0.0, "groups": {}, "growth": {}}
    groups: dict[str, dict[str, float]] = {}
    for row in rows:
        bucket = groups.setdefault(row[group_by], {"units": 0.0, "revenue": 0.0, "returns": 0.0})
        bucket["units"] += row["units"]
        bucket["revenue"] += row["revenue"]
        bucket["returns"] += row["returns"]

    by_quarter: dict[str, float] = {}
    for row in rows:
        by_quarter[row["quarter"]] = by_quarter.get(row["quarter"], 0.0) + row["revenue"]
    quarters = sorted(by_quarter)
    growth: dict[str, float | None] = {}
    for previous, current in zip(quarters, quarters[1:]):
        base = by_quarter[previous]
        growth[f"{previous}->{current}"] = (
            round((by_quarter[current] - base) / base * 100, 2) if base else None
        )

    total_revenue = sum(row["revenue"] for row in rows)
    total_units = sum(row["units"] for row in rows)
    total_returns = sum(row["returns"] for row in rows)
    return {
        "rows": len(rows),
        "total_revenue": round(total_revenue, 2),
        "total_units": round(total_units, 2),
        "return_rate": round(total_returns / total_units, 4) if total_units else 0.0,
        "groups": {
            name: {
                "units": round(values["units"], 2),
                "revenue": round(values["revenue"], 2),
                "share": round(values["revenue"] / total_revenue, 4) if total_revenue else 0.0,
            }
            for name, values in sorted(groups.items())
        },
        "growth": growth,
        "best_group": max(groups.items(), key=lambda item: item[1]["revenue"])[0],
    }


def render_report(profile: dict[str, Any], summary: dict[str, Any], filename: str) -> str:
    lines = [
        f"# Sales report: {filename}",
        "",
        f"Rows analysed: **{summary['rows']}** (columns checked: {len(profile['columns'])}).",
        "",
        "## Totals",
        "",
        f"- Revenue: **{summary['total_revenue']:.2f}**",
        f"- Units: **{summary['total_units']:.0f}**",
        f"- Return rate: **{summary['return_rate']:.2%}**",
        f"- Best region by revenue: **{summary['best_group']}**",
        "",
        "## By region",
        "",
        "| region | units | revenue | share |",
        "| --- | --- | --- | --- |",
    ]
    for name, values in summary["groups"].items():
        lines.append(
            f"| {name} | {values['units']:.0f} | {values['revenue']:.2f} | {values['share']:.1%} |"
        )
    lines += ["", "## Quarter-over-quarter", ""]
    if summary["growth"]:
        for pair, change in summary["growth"].items():
            value = "n/a" if change is None else f"{change:+.2f}%"
            lines.append(f"- {pair}: {value}")
    else:
        lines.append("- not enough quarters to compare")
    lines += ["", "## Data quality", ""]
    if profile["issues"]:
        lines += [f"- {issue}" for issue in profile["issues"]]
    else:
        lines.append("- no problems found")
    return "\n".join(lines) + "\n"


def make_tools(fs: SandboxFS) -> list[ToolSpec]:
    def profile_csv(arguments: dict[str, Any]) -> dict[str, Any]:
        text = fs.read_text(arguments["path"])
        rows, issues = load_rows(text)
        columns = list(csv.DictReader(io.StringIO(text)).fieldnames or [])
        return {
            "columns": columns,
            "rows_usable": len(rows),
            "issues": issues,
            "bytes": len(text.encode("utf-8")),
        }

    def summarize_csv(arguments: dict[str, Any]) -> dict[str, Any]:
        rows, issues = load_rows(fs.read_text(arguments["path"]))
        result = summarize(rows, arguments.get("group_by", "region"))
        result["issues"] = issues
        return result

    def write_report(arguments: dict[str, Any]) -> dict[str, Any]:
        written = fs.write_text(arguments["path"], arguments["markdown"])
        return {"path": arguments["path"], "bytes": written}

    return [
        ToolSpec(
            "profile_csv",
            "Validate a CSV inside the workspace: columns, usable rows, and data-quality issues.",
            profile_csv,
            PROFILE_INPUT,
            output_schema=object_schema(
                {"columns": {"type": "array"}, "rows_usable": {"type": "integer"}}, allow_extra=True
            ),
            side_effect="read",
        ),
        ToolSpec(
            "summarize",
            "Aggregate revenue, units, returns, and growth from a CSV in the workspace.",
            summarize_csv,
            SUMMARY_INPUT,
            output_schema=object_schema({"rows": {"type": "integer"}}, allow_extra=True),
            side_effect="read",
        ),
        ToolSpec(
            "write_report",
            "Write the markdown report into the workspace. Requires approval.",
            write_report,
            WRITE_INPUT,
            output_schema=object_schema({"bytes": {"type": "integer"}}, allow_extra=True),
            side_effect="write",
            requires_approval=True,
        ),
    ]


PLAN = [
    {"tool": "profile_csv", "arguments": {"path": "sales.csv"}},
    {"tool": "summarize", "arguments": {"path": "sales.csv", "group_by": "region"}},
    {"final": "Profile and totals ready."},
]


def prepare_workspace(source: Path, workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "reports").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, workspace / "sales.csv")
    return workspace


def run_analysis(workspace: Path, *, approve: bool = True, filename: str = "sales.csv"):
    workspace = workspace.resolve()
    policy = Policy(
        allowed_tools=frozenset({"profile_csv", "summarize", "write_report"}),
        roots=(workspace,),
        allow_write=True,
        require_approval=frozenset({"write_report"}),
        max_read_bytes=100_000,
        max_write_bytes=20_000,
    )
    fs = SandboxFS(policy, max_read_bytes=100_000, max_write_bytes=20_000)
    registry = ToolRegistry(approver=ScriptedApprover([approve]))
    for spec in make_tools(fs):
        registry.register(spec)
    registry.allow("profile_csv", "summarize", "write_report")

    result = run_agent(
        ScriptedModel(PLAN),
        registry,
        f"Analyse {filename} and report revenue by region.",
        limits=RunLimits(max_steps=5, max_tool_calls=4, timeout_s=5.0),
        policy=policy,
    )

    if not result.ok:
        return result, None

    # The report is rendered by code, not by the model: numbers arrive already
    # validated from the tools, so the agent cannot invent a total.
    profile_result = registry.call("profile_csv", {"path": f"sales.csv"})
    summary_result = registry.call("summarize", {"path": "sales.csv", "group_by": "region"})
    if not (profile_result.ok and summary_result.ok):
        return result, None
    markdown = render_report(profile_result.value, summary_result.value, filename)
    arguments = {"path": "reports/summary.md", "markdown": markdown}
    # The final write goes through the same approval gate as any tool call, and
    # the decision is recorded on the run's trace so a denied write is auditable.
    result.trace.record("approval", "write_report", approved=approve)
    result.trace.record("tool_call", "write_report", step=result.steps, arguments=arguments)
    written = registry.call("write_report", arguments, approval=approve)
    result.trace.record("tool_result", "write_report", written.duration_ms,
                        ok=written.ok, code=written.code)
    return result, (written, markdown)


DEMO_QUERIES = ()


def demo(filename: str, approve: bool) -> int:
    source = DATA_DIR / filename
    if not source.exists():
        print(f"missing {source}; run: python scripts/make_agent_data.py", file=sys.stderr)
        return 2
    workspace = prepare_workspace(source, OUT_DIR)
    result, outcome = run_analysis(workspace, approve=approve)
    print(f"workspace: {workspace}")
    print(f"agent: {result.stop_reason}, {result.steps} steps, {result.tool_calls} tool calls")
    if outcome is None:
        print(result.answer)
        return 1
    written, markdown = outcome
    print(markdown)
    print(f"write: {written.code or 'ok'} (approved={approve})")
    return 0 if written.ok else 1


def selftest() -> int:
    checks = Checks("project D - CSV analyst")
    with tempfile.TemporaryDirectory() as tmp:
        workspace = prepare_workspace(DATA_DIR / "sales.csv", Path(tmp) / "ws")
        result, outcome = run_analysis(workspace, approve=True)
        checks.check("agent completes", result.ok, result.stop_reason)
        checks.check("report written", outcome is not None and outcome[0].ok, str(outcome and outcome[0].error))
        report_path = workspace / "reports" / "summary.md"
        checks.check("file exists on disk", report_path.exists())
        if report_path.exists():
            text = report_path.read_text(encoding="utf-8")
            checks.check("report has totals", "Revenue:" in text and "Return rate:" in text, text[:80])
            checks.check("report has regions", text.count("| north |") == 1, text[:200])

        # Independent arithmetic: recompute the same totals from the CSV here.
        expected_rows, _ = load_rows((DATA_DIR / "sales.csv").read_text(encoding="utf-8"))
        expected_revenue = round(sum(row["revenue"] for row in expected_rows), 2)
        checks.check("report revenue matches an independent sum",
                     f"{expected_revenue:.2f}" in report_path.read_text(encoding="utf-8"),
                     f"expected {expected_revenue}")

    with tempfile.TemporaryDirectory() as tmp:
        workspace = prepare_workspace(DATA_DIR / "sales_messy.csv", Path(tmp) / "ws")
        _, outcome = run_analysis(workspace, approve=True, filename="sales_messy.csv")
        text = (workspace / "reports" / "summary.md").read_text(encoding="utf-8")
        checks.check("messy file: missing revenue reported", "recomputed" in text, text[-300:])
        checks.check("messy file: negative units reported", "negative units" in text)
        checks.check("messy file: duplicate reported", "duplicate" in text)
        checks.check("messy file: report still produced", outcome is not None and outcome[0].ok)

    with tempfile.TemporaryDirectory() as tmp:
        workspace = prepare_workspace(DATA_DIR / "sales.csv", Path(tmp) / "ws")
        result, outcome = run_analysis(workspace, approve=False)
        checks.check("denied approval blocks the write", not (workspace / "reports" / "summary.md").exists())
        denials = [e for e in result.trace.records("approval") if e.data.get("approved") is False]
        checks.check("denial is traced", len(denials) >= 1, f"{len(denials)} denials")

    with tempfile.TemporaryDirectory() as tmp:
        workspace = prepare_workspace(DATA_DIR / "sales.csv", Path(tmp) / "ws")
        policy = Policy(
            allowed_tools=frozenset({"profile_csv"}),
            roots=(workspace.resolve(),),
            allow_write=True,
        )
        fs = SandboxFS(policy)
        registry = ToolRegistry(approver=ScriptedApprover([True]))
        for spec in make_tools(fs):
            registry.register(spec)
        registry.allow("profile_csv", "summarize", "write_report")
        traversal = registry.call("profile_csv", {"path": "../outside.csv"})
        checks.check("path traversal blocked", not traversal.ok, str(traversal.error))
        checks.check("traversal is a policy denial, not a crash",
                     bool(traversal.error and "sandbox" in str(traversal.error.get("message", "")).lower()
                          or "escapes" in str(traversal.error)),
                     str(traversal.error))

        _, issues = load_rows((DATA_DIR / "sales_messy.csv").read_text(encoding="utf-8"))
        joined = " | ".join(issues)
        checks.check(
            "validator reports the three defects",
            len(issues) == 3 and "recomputed" in joined and "negative" in joined
            and "duplicate" in joined,
            str(issues),
        )

    return checks.report()


def main() -> int:
    parser = base_parser("CSV analysis agent that writes a validated report")
    parser.add_argument("--file", default="sales.csv", help="CSV name inside data/agents/csv")
    parser.add_argument("--deny-write", action="store_true", help="simulate a refused approval")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    return demo(args.file, approve=not args.deny_write)


if __name__ == "__main__":
    raise SystemExit(main())
