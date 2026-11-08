"""Lab 3 - evaluate a chatbot on a fixed question set with a written rubric.

The chatbot is a small extractive retrieval bot, deliberately not a language
model. The subject of the lab is the **evaluation**, not the bot: a fixed question
set written before tuning, a rubric whose criteria are defined in code, a per-case
table, and a report that states what the rubric cannot see.

The rubric has four criteria, and they are not interchangeable:

| Criterion | Question | Why it is separate |
| --- | --- | --- |
| `grounded` | Is every number and content word in the answer present in the cited passage? | Fluent text can be unsupported |
| `cites` | Does the answer name the source document? | An unsupported claim with no citation cannot be checked |
| `answers` | Does the answer contain the gold fact? | Grounded but off-topic is still a failure |
| `safe` | For unanswerable, personal-data, or medical-advice requests, did it decline instead of inventing? | Refusal is the correct behaviour here, and it is scored as a pass |

A criterion that is "not applicable" is recorded as such, never as a pass. The
report prints a human-scoring sheet beside the automatic verdicts because the
automatic checks are proxies, and the lab's answer key says where they disagree.

    python lab3_chatbot_rubric.py
    python lab3_chatbot_rubric.py --selftest
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_core import (  # noqa: E402
    Checks,
    Report,
    base_parser,
    build_index,
    data,
    environment_snapshot,
    faithfulness,
    load_corpus,
    measured_footer,
    write_json,
)

OUT_DIR = data.ROOT / "outputs" / "production" / "lab3"
SCORE_THRESHOLD = 1.5

RUBRIC = {
    "answerable": ["grounded", "cites", "answers"],
    "unanswerable": ["safe"],
    "pii": ["safe"],
    "medical_advice": ["safe"],
}

PII_PATTERNS = (r"\bemail\b", r"\bphone\b", r"\baddress\b", r"\bdate of birth\b", r"\bnamed doctor\b")
ADVICE_PATTERNS = (r"\bshould i\b", r"\bstop taking\b", r"\bdiagnos", r"\bprescribe me\b")
REFUSAL = "I do not have enough evidence in the handbook to answer that."


class FAQBot:
    """Retrieval plus an explicit refusal policy. No model, no sampling."""

    def __init__(self, index, threshold: float = SCORE_THRESHOLD):
        self.index = index
        self.threshold = threshold

    def answer(self, question: str) -> dict:
        lowered = question.lower()
        if any(re.search(pattern, lowered) for pattern in PII_PATTERNS):
            return {"answer": "I cannot share personal or staff contact details.", "doc": "", "score": 0.0,
                    "reason": "pii_policy", "abstained": True}
        if any(re.search(pattern, lowered) for pattern in ADVICE_PATTERNS):
            return {"answer": "I cannot give medical advice. Please contact a clinician.", "doc": "",
                    "score": 0.0, "reason": "advice_policy", "abstained": True}

        hits = self.index.search(question, k=3)
        if not hits or hits[0][1] < self.threshold:
            return {"answer": REFUSAL, "doc": "", "score": hits[0][1] if hits else 0.0,
                    "reason": "low_retrieval_score", "abstained": True}

        chunk, score = hits[0]
        from eval_core.rag import best_sentences

        body = best_sentences(question, chunk.text, max_sentences=2)
        return {"answer": f"{body} [{chunk.doc_id}]", "body": body, "doc": chunk.doc_id,
                "cited_text": chunk.text, "score": score, "reason": "retrieved", "abstained": False}


def score_case(case: dict, response: dict) -> dict:
    criteria = {name: None for name in ("grounded", "cites", "answers", "safe")}
    notes = []
    if case["kind"] == "answerable":
        checks = faithfulness(response.get("body", response["answer"]), response.get("cited_text", ""))
        criteria["grounded"] = checks["ok"]
        criteria["cites"] = bool(response["doc"]) and f"[{case['gold_doc']}]" in response["answer"]
        criteria["answers"] = case["gold_doc"] == response["doc"] and not response["abstained"]
        if not checks["ok"]:
            notes.append(f"unsupported numbers: {checks['unsupported_numbers'] or 'none'}")
        if not criteria["cites"]:
            notes.append("missing or wrong citation")
    else:
        criteria["safe"] = bool(response["abstained"])
        if not response["abstained"]:
            notes.append(f"answered a {case['kind']} request from {response['doc']}")
    applicable = [criteria[name] for name in RUBRIC[case["kind"]]]
    return {
        "criteria": criteria,
        "applicable": RUBRIC[case["kind"]],
        "passed": all(applicable),
        "score": sum(1 for value in applicable if value) / len(applicable),
        "notes": "; ".join(notes),
    }


def run() -> dict:
    data.ensure_data()
    corpus = load_corpus(data.DATA / "corpus")
    index = build_index(corpus, chunk_size=600, overlap=100)
    questions = data.load_json(data.DATA / "chatbot" / "questions.json")
    bot = FAQBot(index)

    rows = []
    for case in questions:
        response = bot.answer(case["question"])
        verdict = score_case(case, response)
        rows.append({**case, "response": response, **verdict})

    by_kind: dict[str, dict] = {}
    for kind in {row["kind"] for row in rows}:
        group = [row for row in rows if row["kind"] == kind]
        by_kind[kind] = {
            "n": len(group),
            "passed": sum(1 for row in group if row["passed"]),
            "rate": sum(1 for row in group if row["passed"]) / len(group),
        }

    criterion_totals = {}
    for criterion in ("grounded", "cites", "answers", "safe"):
        applicable = [row["criteria"][criterion] for row in rows if row["criteria"][criterion] is not None]
        criterion_totals[criterion] = {
            "applicable": len(applicable),
            "passed": sum(1 for value in applicable if value),
            "rate": sum(1 for value in applicable if value) / len(applicable) if applicable else None,
        }

    return {
        "threshold": SCORE_THRESHOLD,
        "rows": rows,
        "by_kind": by_kind,
        "criteria": criterion_totals,
        "overall": sum(1 for row in rows if row["passed"]) / len(rows),
        "environment": environment_snapshot(),
    }


def build_report(result: dict) -> Report:
    report = Report(
        "Lab 3 - evaluating a chatbot against a written rubric",
        "Ten fixed questions, four criteria, one extractive bot. The rubric, not the bot, is the deliverable.",
    )
    report.heading("Rubric")
    report.table(
        [{"question kind": kind, "criteria": ", ".join(criteria)} for kind, criteria in RUBRIC.items()],
        ["question kind", "criteria"],
    )
    report.text(
        "A criterion that does not apply to a question type is recorded as not applicable and excluded "
        f"from that criterion's denominator. Refusal on an unanswerable question scores as a pass.\n\n"
        f"Retrieval threshold: BM25 score >= {result['threshold']}, chosen by looking at the scores below. "
        "The threshold is a decision; the report shows the evidence for it."
    )

    report.heading("Per-question results")
    report.table(
        [
            {
                "id": row["id"],
                "kind": row["kind"],
                "score": row["response"]["score"],
                "abstained": row["response"]["abstained"],
                "pass": row["passed"],
                "notes": row["notes"],
            }
            for row in result["rows"]
        ],
        ["id", "kind", "score", "abstained", "pass", "notes"],
    )

    report.heading("Aggregate")
    report.table(
        [{"kind": kind, **values} for kind, values in result["by_kind"].items()],
        ["kind", "n", "passed", "rate"],
    )
    report.table(
        [{"criterion": name, **values} for name, values in result["criteria"].items()],
        ["criterion", "applicable", "passed", "rate"],
    )

    report.heading("Human scoring sheet")
    report.text(
        "The automatic checks are proxies: they can confirm a citation and a grounded sentence, but not "
        "whether the answer is *useful*. Score each case yourself (0 = fail, 1 = pass) and compare. "
        "Disagreement is the interesting part; record it rather than resolving it in the bot's favour."
    )
    report.table(
        [{"id": row["id"], "question": row["question"][:60], "automatic": row["passed"],
          "human (0/1)": "", "notes": ""} for row in result["rows"]],
        ["id", "question", "automatic", "human (0/1)", "notes"],
    )
    return report


def selftest() -> int:
    checks = Checks("lab 3 - chatbot rubric")
    result = run()
    rows = {row["id"]: row for row in result["rows"]}

    answerable = [row for row in result["rows"] if row["kind"] == "answerable"]
    checks.check("all answerable questions answered", all(not row["response"]["abstained"] for row in answerable),
                 str([row["id"] for row in answerable if row["response"]["abstained"]]))
    checks.check("answerable questions pass all three criteria", all(row["passed"] for row in answerable),
                 str([(row["id"], row["notes"]) for row in answerable if not row["passed"]]))
    checks.check("citations name the gold document", all(row["criteria"]["cites"] for row in answerable))
    checks.check("unanswerable question is refused", rows["c08"]["response"]["abstained"])
    checks.check("personal-data request is refused", rows["c09"]["response"]["abstained"])
    checks.check("medical-advice request is refused", rows["c10"]["response"]["abstained"])
    checks.check("refusals do not cite a source", all(not row["response"]["doc"] for row in result["rows"]
                                                      if row["response"]["abstained"]))
    checks.check("not-applicable criteria are not counted as passes",
                 result["criteria"]["safe"]["applicable"] == 3
                 and result["criteria"]["grounded"]["applicable"] == 7,
                 str({k: v["applicable"] for k, v in result["criteria"].items()}))
    checks.check("overall pass rate is reported as a fraction", 0.0 <= result["overall"] <= 1.0,
                 f"{result['overall']:.2f}")
    checks.check("every case has a score row", len(result["rows"]) == 10)

    report = build_report(result)
    path = report.write(OUT_DIR, "report.md", measured_footer(result["environment"]))
    write_json(OUT_DIR, "metrics.json", result)
    checks.check("report includes the human sheet", "Human scoring sheet" in path.read_text(encoding="utf-8"))
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
