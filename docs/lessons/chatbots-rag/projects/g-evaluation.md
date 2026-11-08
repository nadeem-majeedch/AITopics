# Project G - An evaluation harness comparing baseline prompting, RAG, and fine-tuning

**Section path:** [Overview](../index.md) · Modules [CA14](../ca14-evaluation.md), [CA15](../ca15-fine-tuned-models.md) · **Project G** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 15% of the section assessment |
| **Time** | 5 hours |
| **Hardware** | CPU-only for the baseline and RAG legs; GPU only for the fine-tuned leg |
| **Code** | `projects/chatbots-rag/project_g_evaluation.py` |
| **Prerequisite** | CA14 |

## The task

Build a harness that scores several systems on one fixed question set and writes a JSON
report. Then use it to answer a specific question: **does retrieval actually help, and
where does it fail?**

The fine-tuned leg is optional. A harness that records it as `skipped` is correct; a
harness that invents a row is not.

## Run the reference implementation

```bash
cd projects/chatbots-rag
python project_g_evaluation.py --selftest
python project_g_evaluation.py --split test
```

Verified output shape:

```text
system          answer  answerable  abstain   false   hit@k       ms
--------------------------------------------------------------------
prompt-only      0.000       0.000      n/a     n/a   0.000    0.011
bm25             0.667       0.667      n/a     n/a   1.000    0.842
vector           0.500       0.500      n/a     n/a   1.000    0.773
hybrid           0.667       0.667      n/a     n/a   1.000    0.764

fine-tuned leg: skipped
```

The `n/a` abstention columns appear because the selftest uses six questions, none of them
unanswerable. Use `--split test` for the full picture.

## What to submit

```text
ca-project-g/
  README.md            # what is compared, settings, how to reproduce
  evaluate.py          # your harness
  questions.json       # your question set with gold evidence
  report.json          # machine-readable results
  report.md            # the human-readable table plus error analysis
  reflection.md        # 200-300 words
```

## Steps

1. **Write 20 questions** before looking at any results: at least 4 unanswerable, at least
   2 whose answer spans two documents, at least 1 adversarial.
2. **Record gold evidence** as document ids, and `must_contain` phrases taken from the
   source text, not the prompt.
3. **Score four configurations**: no retrieval, BM25, dense, hybrid.
4. **Add the fine-tuned leg** only if you have a checkpoint; otherwise let it report
   `skipped` and say why in the report.
5. **Classify every failure** with the taxonomy in CA14.
6. **Report counts as well as rates**: "9 of 12", not only "0.75".
7. **State one change you would make next**, supported by the failure table.

## Expected behaviour

| Observation | Interpretation |
| --- | --- |
| `hit@k` is 1.0 but accuracy is not | Retrieval is fine; generation or the client is the problem |
| Prompt-only scores 0.0 | Correct for a client with no parametric knowledge and a refusal policy |
| Dense alone is worse than BM25 | The embedder captures surface form, not meaning |
| Hybrid equals the better component | The retrievers fail on the same questions |
| Fine-tuned leg absent | `finetuned_leg: skipped` in the report |

## Test cases to include

| # | Case | Pass condition |
| --- | --- | --- |
| 1 | All four legs run | Each produces an aggregate block |
| 2 | Unanswerable items present | `abstention_correct` is a number, not `n/a` |
| 3 | One deliberately broken question | Scored as a failure, not silently skipped |
| 4 | Report serialises | `report.json` reloads and matches the table |
| 5 | Fine-tuned leg absent | Recorded as skipped, no fabricated metrics |

## Constraints

- Same question set, same `k`, same prompt for every leg. One variable at a time.
- Never tune on the test split, then report test numbers as if untouched.
- Do not report a metric whose denominator is zero as `0.0`; report `n/a` and explain.
- Do not include an answer you did not generate in this run.

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Experimental design | 30 | One variable per comparison, splits respected | Several changes at once, test split tuned |
| Metric choice | 25 | Retrieval and generation separated; refusal scored | A single accuracy number |
| Error analysis | 25 | Every failure categorised with a cause | Failures listed without diagnosis |
| Reproducibility | 10 | Report includes settings, counts, model ids | Rates only |
| Honesty | 10 | Skipped legs and small-sample limits stated | Missing legs hidden, overclaimed |

## Extension tasks

1. **Sweep `k`** from 1 to 8 and plot accuracy, precision, and latency against it. State
   the point where extra context stops paying.
2. **Sweep `min_score`** from 0.0 to 0.5 and plot the trade between answering and inventing.
3. **Add a second question set** written by someone else, and report how much your accuracy
   changes. This is the cheapest available proxy for overfitting to your own phrasings.

Next: [Project H](h-domain-assistant.md).
