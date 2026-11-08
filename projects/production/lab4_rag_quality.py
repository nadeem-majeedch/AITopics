"""Lab 4 - retrieval quality and answer faithfulness for a RAG pipeline.

Two families of metric, because a RAG system fails in two different places:

**Retrieval** - recall@k, MRR, nDCG@k against a gold document per question.
If the right text is not in the context, the generator can only guess.

**Faithfulness** - every number in the answer appears in the passage it cites,
content words are present in that passage, and each answer sentence is supported
by it. This catches an answer that is grounded in *something* but not in what it
claims to cite.

The lab sweeps chunk size, because chunking changes both and is usually chosen by
habit rather than measurement.

    python lab4_rag_quality.py
    python lab4_rag_quality.py --selftest
"""

from __future__ import annotations

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
    evaluate_answers,
    load_corpus,
    measured_footer,
    retrieval_report,
    write_json,
)

OUT_DIR = data.ROOT / "outputs" / "production" / "lab4"
CONFIGS = ((200, 0, 0), (200, 0, 12), (600, 100, 12))
K = 3


def no_retrieval_baseline(qa: list[dict]) -> dict:
    """What an answer without evidence scores: nothing, by definition."""
    from eval_core.rag import faithfulness

    rows = []
    for item in qa:
        checks = faithfulness("", "")
        rows.append({"id": item["id"], "faithful": False, "answer_ok": False,
                     "unsupported_numbers": checks["unsupported_numbers"]})
    return {"rows": rows, "retrieval_accuracy": 0.0, "faithfulness": 0.0, "answer_accuracy": 0.0,
            "mean_coverage": 0.0}


def run() -> dict:
    data.ensure_data()
    corpus = load_corpus(data.DATA / "corpus")
    qa = data.load_json(data.DATA / "corpus" / "qa.json")

    configurations = []
    for chunk_size, overlap, min_tokens in CONFIGS:
        index = build_index(corpus, chunk_size=chunk_size, overlap=overlap, min_tokens=min_tokens)
        retrieval = retrieval_report(index, qa, k=K)
        answers = evaluate_answers(index, qa, k=K)
        configurations.append(
            {
                "chunk_size": chunk_size,
                "overlap": overlap,
                "min_tokens": min_tokens,
                "chunks": len(index.chunks),
                "retrieval": {
                    "recall_at_k": retrieval["recall_at_k"],
                    "mrr": retrieval["mrr"],
                    "ndcg_at_k": retrieval["ndcg_at_k"],
                    "top1_accuracy": retrieval["top1_accuracy"],
                },
                "answers": {
                    "faithfulness": answers["faithfulness"],
                    "answer_accuracy": answers["answer_accuracy"],
                    "mean_coverage": answers["mean_coverage"],
                },
                "rows": answers["rows"],
                "retrieval_rows": retrieval["rows"],
            }
        )

    return {
        "k": K,
        "configurations": configurations,
        "baseline": no_retrieval_baseline(qa),
        "environment": environment_snapshot(),
    }


def build_report(result: dict) -> Report:
    report = Report(
        "Lab 4 - retrieval quality and answer faithfulness",
        f"{len(result['configurations'][0]['rows'])} questions with a gold document, three chunking configurations, k = {result['k']}.",
    )
    report.heading("Metrics used")
    report.bullets([
        "**recall@k** - share of questions whose gold document is in the top k.",
        "**MRR** - mean of 1/rank of the first relevant result.",
        "**nDCG@k** - rank-weighted credit, normalised by the ideal ordering.",
        "**faithfulness** - grounded *and* the right document: every number supported, content-word coverage "
        ">= 0.90, and every answer sentence supported by the cited passage.",
    ])

    report.heading("Retrieval and answer quality by configuration")
    report.table(
        [
            {
                "chunk": config["chunk_size"],
                "min tokens": config["min_tokens"],
                "overlap": config["overlap"],
                "chunks": config["chunks"],
                "recall@k": config["retrieval"]["recall_at_k"],
                "MRR": config["retrieval"]["mrr"],
                "nDCG@k": config["retrieval"]["ndcg_at_k"],
                "faithfulness": config["answers"]["faithfulness"],
                "answer accuracy": config["answers"]["answer_accuracy"],
            }
            for config in result["configurations"]
        ],
        ["chunk", "min tokens", "overlap", "chunks", "recall@k", "MRR", "nDCG@k", "faithfulness",
         "answer accuracy"],
    )
    report.text(
        f"No-retrieval baseline: faithfulness {result['baseline']['faithfulness']:.3f}, "
        f"answer accuracy {result['baseline']['answer_accuracy']:.3f}. Any system that scores near this has "
        "not been shown to use its evidence."
    )

    worst = min(result["configurations"], key=lambda c: c["answers"]["faithfulness"])
    configs_by_key = {(c["chunk_size"], c["min_tokens"]): c for c in result["configurations"]}
    failures = [row for row in worst["rows"] if not row["faithful"]]
    report.heading(f"Where the weakest configuration failed (chunk {worst['chunk_size']})")
    if failures:
        report.table(
            [{"id": row["id"], "retrieved": row["retrieved"], "answer_ok": row["answer_ok"],
              "unsupported": ", ".join(row["unsupported_numbers"]) or "none",
              "answer": row["answer"]} for row in failures],
            ["id", "retrieved", "answer_ok", "unsupported", "answer"],
        )
        report.text(
            "With 200-character chunks and no overlap, the section that holds the answer is cut into "
            "fragments. The fragment that ranked first for this question contained no complete sentence, so "
            "the extractor returned an empty answer and the rubric scored it zero. Recall@3 was still "
            f"{configs_by_key[(200, 0)]['retrieval']['recall_at_k']:.3f}: retrieval looked perfect. Dropping "
            "chunks with fewer than 12 content tokens repairs the answer at the same chunk size: faithfulness "
            f"{configs_by_key[(200, 0)]['answers']['faithfulness']:.3f} to "
            f"{configs_by_key[(200, 12)]['answers']['faithfulness']:.3f}, and answer accuracy "
            f"{configs_by_key[(200, 0)]['answers']['answer_accuracy']:.3f} to "
            f"{configs_by_key[(200, 12)]['answers']['answer_accuracy']:.3f}. At 600 characters with overlap, "
            "the fact and the sentence around it stay in one chunk and both reach 1.000."
        )
    else:
        report.text("No failures in the weakest configuration on this question set. That is a floor, not proof.")

    report.heading("Limits of this measurement")
    report.bullets([
        "Six documents and eight questions: retrieval saturates quickly, so recall@k cannot separate the "
        "configurations. Faithfulness is the metric that moved.",
        "Gold documents were assigned by hand. A different annotator could reasonably choose a different "
        "document for a multi-part question.",
        "Faithfulness is lexical. A correct paraphrase that introduces a new word fails the coverage check; "
        "a copied but irrelevant sentence can pass. Report the raw checks with any score.",
    ])
    return report


def selftest() -> int:
    checks = Checks("lab 4 - RAG quality")
    result = run()
    configs_by_key = {(c["chunk_size"], c["min_tokens"]): c for c in result["configurations"]}

    checks.equal("three configurations measured", len(result["configurations"]), len(CONFIGS))
    checks.check("smaller chunks produce more chunks",
                 configs_by_key[(200, 0)]["chunks"] > configs_by_key[(600, 12)]["chunks"],
                 f"{configs_by_key[(200, 0)]['chunks']} vs {configs_by_key[(600, 12)]['chunks']}")
    checks.check("retrieval is strong on this corpus",
                 configs_by_key[(600, 12)]["retrieval"]["recall_at_k"] >= 0.875,
                 f"{configs_by_key[(600, 12)]['retrieval']['recall_at_k']:.3f}")
    checks.check("MRR and nDCG are in range",
                 all(0.0 <= config["retrieval"][metric] <= 1.0
                     for config in result["configurations"] for metric in ("mrr", "ndcg_at_k")))
    checks.check("large chunks are faithful",
                 configs_by_key[(600, 12)]["answers"]["faithfulness"] >= 0.875,
                 f"{configs_by_key[(600, 12)]['answers']['faithfulness']:.3f}")
    checks.check("chunking changed answer quality",
                 configs_by_key[(200, 0)]["answers"]["faithfulness"]
                 <= configs_by_key[(600, 12)]["answers"]["faithfulness"],
                 f"{configs_by_key[(200, 0)]['answers']['faithfulness']:.3f} vs "
                 f"{configs_by_key[(600, 12)]['answers']['faithfulness']:.3f}")
    checks.check("no-retrieval baseline is zero",
                 result["baseline"]["faithfulness"] == 0.0 and result["baseline"]["answer_accuracy"] == 0.0)
    checks.check("per-question rows exist for every config",
                 all(len(config["rows"]) == 8 for config in result["configurations"]))
    failed = [row for row in configs_by_key[(200, 0)]["rows"] if not row["faithful"]]
    checks.check("small chunks without overlap or a length filter lose an answer",
                 bool(failed) and all(row["retrieved"] for row in failed),
                 str([row["id"] for row in failed]))
    checks.check("the length filter repairs it",
                 configs_by_key[(200, 0)]["answers"]["faithfulness"]
                 < configs_by_key[(200, 12)]["answers"]["faithfulness"],
                 f"{configs_by_key[(200, 0)]['answers']['faithfulness']:.3f} -> "
                 f"{configs_by_key[(200, 12)]['answers']['faithfulness']:.3f}")

    report = build_report(result)
    path = report.write(OUT_DIR, "report.md", measured_footer(result["environment"]))
    write_json(OUT_DIR, "metrics.json", result)
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
