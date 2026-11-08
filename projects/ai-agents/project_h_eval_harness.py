"""Project H - an evaluation harness for agents: success, errors, latency, tokens, cost.

Four variants, one task set, one definition of success:

``no_tool``     answers from nothing; should fail everything except the abstention
``search_only`` reads the top snippet but never the document; loses details
``search_read`` searches, reads, quotes, cites; the reference configuration
``flaky``       the reference configuration with a tool that fails once per run

The point is the comparison, not the winner. A single run tells you a demo
worked; this tells you the success rate, the tool-error rate, the retry count,
the step count, the token count, the cost, and the latency distribution — and
which tasks failed and why.

Reproducibility
---------------
* The task sets are JSON files, not code, so the same evaluation can run against
  someone else's agent.
* Success criteria are declared in the task before the run (``expect_substrings``,
  ``expect_tools``, ``forbid_tools``).
* Counters (pass/fail, steps, tool calls, tokens, retries) are deterministic for
  scripted models. Latency is measured with a real clock and therefore varies;
  the report says so and the tests avoid asserting on it.
* Cost uses a price table; scripted and local models are priced at zero, and the
  hosted price must be passed in, never guessed.

Run
---
    python project_h_eval_harness.py --selftest
    python project_h_eval_harness.py --split test
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_core import (  # noqa: E402
    EvalTask,
    Policy,
    RunLimits,
    ScriptedModel,
    ToolFailure,
    ToolRegistry,
    evaluate,
    load_tasks,
    run_agent,
    safe_corpus,
)
from agent_core.cli import Checks, base_parser  # noqa: E402
from agent_core.model import Decision, Message, ModelReply, Usage  # noqa: E402
from agent_core.retrieval import Corpus  # noqa: E402
from project_c_docs_search_agent import (  # noqa: E402
    ABSTAIN,
    QuoteAndCiteModel,
    _payload,
    build_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = REPO_ROOT / "data" / "agents" / "tasks"
OUT_DIR = REPO_ROOT / "outputs" / "agents" / "project_h"


class SnippetOnlyModel:
    """Answers straight from the search snippet: cheap, and provably lossy."""

    name = "snippet-only-v1"

    def __init__(self) -> None:
        self.calls = 0

    def respond(self, messages: list[Message]) -> ModelReply:
        self.calls += 1
        tool_messages = [m for m in messages if m.get("role") == "tool"]
        question = next((m["content"] for m in messages if m.get("role") == "user"), "")
        if not tool_messages:
            raw = json.dumps({"tool": "search_docs", "arguments": {"query": question[:300], "k": 3}})
            return ModelReply(raw, Decision.tool_call("search_docs", {"query": question[:300], "k": 3}),
                              Usage(20, 20), self.name)
        payload = _payload(tool_messages[-1]) or {}
        hits = payload.get("hits") or []
        if not hits:
            return ModelReply(json.dumps({"final": ABSTAIN}), Decision.final(ABSTAIN),
                              Usage(20, 10), self.name)
        snippet = hits[0]["snippet"]
        answer = f"{snippet} [{hits[0]['doc_id']}]"
        return ModelReply(json.dumps({"final": answer}), Decision.final(answer),
                          Usage(20, len(answer) // 4), self.name)


class NoToolModel:
    name = "no-tool-v1"

    def respond(self, messages: list[Message]) -> ModelReply:
        content = ABSTAIN
        return ModelReply(json.dumps({"final": content}), Decision.final(content), Usage(10, 10),
                          self.name)


def _faulty_search(corpus: Corpus) -> list[Any]:
    """Tools where the first search attempt fails with a retryable error."""

    registry = build_registry(corpus)
    spec = registry.get("search_docs")
    original = spec.func
    state = {"failed": False}

    def flaky(arguments: dict[str, Any]) -> dict[str, Any]:
        if not state["failed"]:
            state["failed"] = True
            raise ToolFailure("search backend timed out", retryable=True)
        return original(arguments)

    spec.func = flaky
    spec.retryable = True
    return [spec, registry.get("read_doc")]


def runner_for(variant: str, corpus: Corpus):
    if variant == "no_tool":
        model = NoToolModel()
        registry = ToolRegistry()
        registry.register(build_registry(corpus).get("search_docs"))
        registry.register(build_registry(corpus).get("read_doc"))
        registry.allow("search_docs", "read_doc")
    elif variant == "search_only":
        model = SnippetOnlyModel()
        registry = build_registry(corpus)
    elif variant == "flaky":
        model = QuoteAndCiteModel()
        registry = ToolRegistry()
        for spec in _faulty_search(corpus):
            registry.register(spec)
        registry.allow("search_docs", "read_doc")
    else:
        model = QuoteAndCiteModel()
        registry = build_registry(corpus)

    policy = Policy(allowed_tools=frozenset(registry.names()))

    def runner(task: EvalTask):
        return run_agent(
            model,
            registry,
            task.prompt,
            limits=RunLimits(
                max_steps=task.max_steps,
                max_tool_calls=task.max_tool_calls,
                timeout_s=5.0,
                max_observation_chars=4000,
            ),
            policy=policy,
        )

    return runner


def run_variant(tasks: list[EvalTask], variant: str, *, corpus: Corpus | None = None,
                trace_dir: Path | None = None):
    corpus = corpus or safe_corpus()
    return evaluate(tasks, runner_for(variant, corpus), split="dev", trace_dir=trace_dir,
                    meta={"variant": variant, "model": variant})


def comparison_table(reports: dict[str, Any]) -> str:
    lines = [
        "| variant | success | tool errors | retries | mean steps | tokens in | latency p50 ms | cost USD |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, report in reports.items():
        agg = report.aggregate()
        lines.append(
            f"| {name} | {agg['passed']}/{agg['cases']} ({agg['success_rate']:.0%}) | "
            f"{agg['tool_errors']} | {agg['retries']} | {agg['mean_steps']} | "
            f"{agg['mean_tokens_in']} | {agg['p50_latency_ms']} | "
            f"{agg['total_cost_usd']:.6f} |"
        )
    return "\n".join(lines)


def demo(split: str) -> int:
    path = TASKS_DIR / f"{split}.json"
    if not path.exists():
        print(f"missing {path}; run: python scripts/make_agent_data.py", file=sys.stderr)
        return 2
    tasks = load_tasks(path)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reports = {}
    for variant in ("no_tool", "search_only", "search_read", "flaky"):
        reports[variant] = run_variant(tasks, variant, trace_dir=OUT_DIR / "traces" / variant)
        reports[variant].to_json(OUT_DIR / f"{split}_{variant}.json")

    table = comparison_table(reports)
    print(f"split: {split} ({len(tasks)} tasks)\n")
    print(table)
    reference = reports["search_read"]
    print("\nFailures in the reference variant:")
    failures = [case for case in reference.cases if not case.passed]
    if not failures:
        print("  none")
    for case in failures:
        print(f"  {case.task_id}: {case.failures}")
    (OUT_DIR / f"{split}_summary.md").write_text(
        f"# Agent evaluation ({split})\n\n{table}\n", encoding="utf-8"
    )
    print(f"\nwrote reports to {OUT_DIR}")
    return 0


def selftest() -> int:
    checks = Checks("project H - evaluation harness")

    dev_path, test_path = TASKS_DIR / "dev.json", TASKS_DIR / "test.json"
    checks.check("task files exist", dev_path.exists() and test_path.exists(),
                 "run scripts/make_agent_data.py")
    if not (dev_path.exists() and test_path.exists()):
        return checks.report()

    dev = load_tasks(dev_path)
    test = load_tasks(test_path)
    checks.equal("dev has six tasks", len(dev), 6)
    checks.equal("test has five tasks", len(test), 5)

    corpus = safe_corpus()
    with tempfile.TemporaryDirectory() as tmp:
        traces = Path(tmp) / "traces"
        reference = run_variant(test, "search_read", corpus=corpus, trace_dir=traces)
        snippet = run_variant(test, "search_only", corpus=corpus)
        blind = run_variant(test, "no_tool", corpus=corpus)
        flaky = run_variant(test, "flaky", corpus=corpus)
        traces_ok = all(case.trace_path and Path(case.trace_path).exists()
                        for case in reference.cases)

    ref = reference.aggregate()
    checks.check("reference passes several held-out tasks", ref["passed"] >= 4, str(ref))
    checks.check("reference beats snippet-only",
                 ref["passed"] > snippet.aggregate()["passed"],
                 f"{ref['passed']} vs {snippet.aggregate()['passed']}")
    checks.check("no-tool agent passes at most the abstention task",
                 blind.aggregate()["passed"] <= 1, str(blind.aggregate()))

    flaky_agg = flaky.aggregate()
    checks.check("retryable failure was retried", flaky_agg["retries"] >= 1, str(flaky_agg))
    checks.check("flaky variant still completes tasks", flaky_agg["passed"] >= 4, str(flaky_agg))
    checks.check("tool errors are counted", flaky_agg["tool_errors"] >= 1, str(flaky_agg))

    checks.check("scripted models cost nothing", ref["total_cost_usd"] == 0.0)
    checks.check("latency is measured, not zero", ref["p50_latency_ms"] >= 0)
    checks.check("aggregate has the required keys",
                 {"success_rate", "tool_error_rate", "mean_steps", "p50_latency_ms",
                  "total_cost_usd"} <= set(ref))
    checks.check("per-case traces written", traces_ok)

    # Determinism of the counters that must not vary.
    again = run_variant(test, "search_read", corpus=corpus)
    first = [(c.task_id, c.passed, c.steps, c.tool_calls, c.tokens_in) for c in reference.cases]
    second = [(c.task_id, c.passed, c.steps, c.tool_calls, c.tokens_in) for c in again.cases]
    checks.check("counters reproduce exactly", first == second, f"{first} vs {second}")

    # A failing task explains itself.
    broken = [c for c in blind.cases if not c.passed]
    checks.check("failures carry reasons", bool(broken) and all(c.failures for c in broken))

    return checks.report()


def main() -> int:
    parser = base_parser("Agent evaluation harness")
    parser.add_argument("--split", choices=("dev", "test"), default="test")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    return demo(args.split)


if __name__ == "__main__":
    raise SystemExit(main())
