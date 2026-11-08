"""Project G - An evaluation harness comparing prompting, RAG, and fine-tuning.

The claim "RAG is better" is not an evaluation. This harness scores several
configurations on the *same* fixed question set and writes a JSON report, so a
reader can reproduce the comparison or disagree with it precisely.

Configurations compared by default (all offline):

===============  ==========================================================
name             what it is
===============  ==========================================================
prompt-only      no retrieval at all; the model must answer from memory
bm25             lexical retrieval only (vector weight 0.0)
vector           dense retrieval only (vector weight 1.0)
hybrid           dense plus lexical fusion (the default pipeline)
===============  ==========================================================

The fine-tuned leg is optional and explicit: pass ``--finetuned-model`` with a
local path or model id. Without it the report records the leg as skipped, because
a missing experiment is a fact about the study, not a zero.

Run:
    python project_g_evaluation.py --split test
    python project_g_evaluation.py --split test --out outputs/eval.json
    python project_g_evaluation.py --selftest

Read the metrics in this order: ``hit_at_k`` (did retrieval find it),
``answer_accuracy_answerable`` (did the answer state it), ``false_answer_rate_
unanswerable`` (did it invent), then latency.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from chatbot_core import (
    ABSTAIN_TEXT,
    Answer,
    FakeModelClient,
    GenerationConfig,
    RAGChatbot,
    evaluate,
    format_table,
    load_questions,
    write_report,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA = REPO_ROOT / "data" / "chatbots-rag"
CORPUS = DATA / "corpus"


class PromptOnlyBot:
    """Adapter that answers with no evidence, to make the baseline explicit.

    With the offline client this always refuses: it has nothing to quote. That is
    the honest result for a memory-only system in this harness. With a real model
    the same leg is the interesting comparison, because it will answer from
    parametric knowledge and sometimes be wrong without saying so.
    """

    def __init__(self, client=None) -> None:
        self.client = client or FakeModelClient()
        self.config = GenerationConfig(k=0)

    def retrieve_doc_ids(self, question: str, k: int | None = None) -> list[str]:
        return []

    def ask(self, question: str, use_history: bool = False) -> Answer:
        text = self.client.complete(
            [
                {"role": "system", "content": "Answer from memory. If unsure, say so."},
                {"role": "user", "content": question},
            ]
        )
        abstained = ABSTAIN_TEXT in text or not text.strip()
        return Answer(text=text.strip() or ABSTAIN_TEXT, abstained=abstained, model=self.client.name)


def build_systems() -> dict[str, object]:
    common = dict(config=GenerationConfig(k=4, min_score=0.12))
    return {
        "prompt-only": PromptOnlyBot(),
        "bm25": RAGChatbot.from_directory(CORPUS, vector_weight=0.0, **common),
        "vector": RAGChatbot.from_directory(CORPUS, vector_weight=1.0, **common),
        "hybrid": RAGChatbot.from_directory(CORPUS, vector_weight=0.6, **common),
    }


def run(split: str = "test", finetuned_model: str | None = None) -> dict:
    questions = load_questions(DATA / f"{split}_questions.json")
    systems = build_systems()

    if finetuned_model:
        from chatbot_core import LocalTransformersClient

        try:
            client = LocalTransformersClient(finetuned_model)
        except Exception as exc:  # noqa: BLE001 - a skipped leg must be reported
            print(f"fine-tuned leg skipped: {type(exc).__name__}: {exc}")
        else:
            systems["hybrid+finetuned"] = RAGChatbot.from_directory(
                CORPUS,
                client=client,
                config=GenerationConfig(k=4, min_score=0.12),
            )

    report = {
        "split": split,
        "questions": len(questions),
        "systems": {name: evaluate(bot, questions, name=name) for name, bot in systems.items()},
        "finetuned_leg": "included" if "hybrid+finetuned" in systems else "skipped",
    }
    return report


def summarize(report: dict) -> str:
    rows = []
    for name, payload in report["systems"].items():
        aggregate = payload["aggregate"]
        rows.append(
            {
                "system": name,
                "answer_accuracy": aggregate["answer_accuracy"],
                "answerable": aggregate["answer_accuracy_answerable"],
                "abstention": aggregate["abstention_correct"],
                "false_answer": aggregate["false_answer_rate_unanswerable"],
                "hit_at_k": aggregate["hit_at_k"],
                "latency_ms": aggregate["mean_latency_ms"],
            }
        )

    header = f"{'system':<14}{'answer':>8}{'answerable':>12}{'abstain':>9}{'false':>8}{'hit@k':>8}{'ms':>9}"
    lines = [header, "-" * len(header)]
    for row in rows:
        def fmt(value):
            return "n/a" if value is None else f"{value:.3f}"

        lines.append(
            f"{row['system']:<14}{fmt(row['answer_accuracy']):>8}{fmt(row['answerable']):>12}"
            f"{fmt(row['abstention']):>9}{fmt(row['false_answer']):>8}{fmt(row['hit_at_k']):>8}"
            f"{fmt(row['latency_ms']):>9}"
        )
    lines.append("")
    lines.append(f"fine-tuned leg: {report['finetuned_leg']}")
    return "\n".join(lines)


def selftest() -> int:
    questions = load_questions(DATA / "test_questions.json")[:6]
    systems = build_systems()
    report = {"split": "selftest", "questions": len(questions),
              "systems": {name: evaluate(bot, questions, name=name) for name, bot in systems.items()},
              "finetuned_leg": "skipped"}
    print(summarize(report))

    failures = 0
    base = report["systems"]["prompt-only"]["aggregate"]
    rag = report["systems"]["hybrid"]["aggregate"]
    if base["false_answer_rate_unanswerable"] not in (None, 0.0):
        print("FAIL  prompt-only baseline invented an answer")
        failures += 1
    if rag["hit_at_k"] is None or rag["hit_at_k"] < 0.5:
        print("FAIL  hybrid retrieval hit rate below 0.5 on the sample")
        failures += 1
    print(f"\n{failures} failure(s)")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Project G: evaluation harness")
    parser.add_argument("--split", default="test", choices=["dev", "test"])
    parser.add_argument("--finetuned-model", default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    report = run(args.split, args.finetuned_model)
    print(summarize(report))
    out = args.out or REPO_ROOT / "outputs" / f"chatbot_eval_{args.split}.json"
    write_report(report, out)
    print(f"\nreport: {out}")

    for name, payload in report["systems"].items():
        print()
        print(format_table(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
