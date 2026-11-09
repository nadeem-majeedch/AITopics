# CA14 - RAG evaluation and error analysis {#ca14}

**Section path:** [Overview](index.md) · **Module 14** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h Project G |
| **Hardware** | CPU-only |
| **Prerequisites** | CA12, CA13 |
| **You will produce** | A reproducible evaluation report with per-question rows and an error taxonomy |

## Why this module exists

Every earlier module ended with a claim. This one replaces claims with numbers.

"I asked it ten questions and the answers looked good" is not an evaluation, because it
cannot be repeated, compared, or disagreed with. A fixed question set with gold evidence
and documented metrics can be all three.

## The question set is the instrument

Each item in `data/chatbots-rag/test_questions.json` has four fields:

```json
{
  "id": "t02",
  "question": "Do purchased credits expire?",
  "answerable": true,
  "gold_doc_ids": ["billing-and-refunds"],
  "must_contain": ["never expire"]
}
```

| Field | Purpose | Common mistake |
| --- | --- | --- |
| `answerable` | Separates answer and refusal scoring | Everything marked answerable |
| `gold_doc_ids` | Scores retrieval independently | Gold document is the one you tuned on |
| `must_contain` | A cheap, checkable correctness proxy | Phrase taken from the prompt, not the source |

**Write the set before tuning.** If you add a question after seeing a failure and then
tune until it passes, you have measured your tuning, not your system. Keep a `dev` split
for iteration and a `test` split you touch last. This section ships both: 14 dev
questions and 12 test questions.

`must_contain` is a proxy, and a weak one: it detects a missing fact, not a wrong one
stated confidently. Say so in your report rather than presenting it as correctness.

## The metrics, and what each one isolates

| Metric | Formula (in this harness) | What it isolates |
| --- | --- | --- |
| `hit_at_k` | Gold document in top `k` | Retrieval |
| `answer_accuracy` | All `must_contain` present and not refused | End-to-end |
| `answer_accuracy_answerable` | Same, answerable items only | Generation |
| `abstention_correct` | Refused on unanswerable items | Refusal policy |
| `false_answer_rate_unanswerable` | Answered anyway on unanswerable items | The dangerous failure |
| `citation_precision` | Cited documents that are gold / all cited | Citation discipline |
| `citation_recall` | Gold documents that were cited / all gold | Coverage |
| `mean_latency_ms` | Wall clock per question | Cost |

Run it:

```bash
cd projects/chatbots-rag
python project_g_evaluation.py --split test
```

## Measured results

From the authoring run (Windows 11, Python 3.12.10, CPU only, offline extractive client,
hashing embeddings, `k=4`, `min_score=0.12`):

| Metric | Dev (n=14) | Test (n=12) |
| --- | --- | --- |
| `answer_accuracy` | 1.0000 | 0.7500 |
| `answer_accuracy_answerable` | 1.0000 | 0.7000 |
| `abstention_correct` | 1.0000 | 1.0000 |
| `false_answer_rate_unanswerable` | 0.0000 | 0.0000 |
| `citation_precision` | 1.0000 | 1.0000 |
| `citation_recall` | 1.0000 | 0.8000 |
| `hit_at_k` | 1.0000 | 1.0000 |
| `mean_latency_ms` | 0.804 | 0.775 |

**Read the first row against the seventh.** Retrieval found a gold document for every
answerable question in both splits (`hit_at_k = 1.0000`). The dev split answered all
of them; the held-out test split still missed three of twelve. That remaining gap is
not retrieval, so tuning retrieval would not close it.

**Read the refusal rows.** `abstention_correct = 1.0000` and
`false_answer_rate = 0.0000` mean every unanswerable question produced a refusal. This
system is conservative, which is the right bias for a cited assistant and the wrong one
for, say, a brainstorming tool.

These numbers describe *this* pipeline: an extractive stand-in model and a hashing
embedder. They are not claims about language models. With a real instruct model and a
trained embedder, expect `answer_accuracy` to rise and `abstention_correct` to fall —
the second is the trade you must watch.

## Error analysis: the failures are the deliverable

The dev split has no failures. Three held-out test questions fail, and each failure
has a specific cause:

| Item | Question | Failure | Cause |
| --- | --- | --- | --- |
| t05 | Can I get my data deleted? | Refused | Inflection mismatch: the source says "deletion", the question says "deleted" |
| t06 | Should I fine-tune to teach facts? | Answered from a weaker section | "Using both" shared two content words; "What fine-tuning changes" shared two as well |
| t07 | What must a citation point to? | Refused | The question's verbs ("point to") do not appear in the source sentence |

Two are **over-refusal** and one is **misattribution**. That is a diagnosis, and it
points at the extractive client, not at the architecture: the pipeline correctly
retrieved the gold document and correctly refused to cite something unsupported.

Contrast a report that says "accuracy is 75%". It cannot tell you whether to improve
retrieval, the model, or the prompt. This table can.

## The error taxonomy to use

| Category | Definition | Detected by |
| --- | --- | --- |
| Retrieval miss | Gold document not in top `k` | `hit_at_k = false` |
| Over-refusal | Refused although evidence supported an answer | `abstained` on an answerable item |
| Under-refusal | Answered an unanswerable question | `false_answer_rate > 0` |
| Misattribution | Right topic, wrong section quoted | Human review of the cited chunk |
| Fabrication | Claim not supported by any cited chunk | Human review; the validator catches invented ids only |
| Citation error | Cited document is not the supporting one | `citation_precision < 1` |
| Format failure | Unparseable output, wrong language | Parse errors in the log |

Automated metrics find the first three, the last one, and part of the sixth. **Human
review is required for misattribution and fabrication** — the two most damaging — and
that is why a report needs at least twenty hand-checked answers.

## Comparing systems without fooling yourself

```bash
python project_g_evaluation.py --split test --out outputs/eval_test.json
```

Changes must be compared on the same split, the same `k`, and the same prompt. Vary one
thing:

| Change | Expect to move | If it does not, why? |
| --- | --- | --- |
| Better embedder | `hit_at_k`, `answer_accuracy` | Retrieval was already at 1.0 |
| Larger `k` | recall up, precision down, latency up | Context budget or noise |
| Lower `min_score` | answers up, `false_answer_rate` up | The threshold was doing the work |
| Stricter prompt | fabrication down, over-refusal up | The model obeyed |
| Fine-tuned model | style; refusal rate may drop | Not a knowledge change |

That last row is the finding students miss: fine-tuning for style commonly *reduces*
refusal behaviour, because refusal examples are rare in training data. Watch
`false_answer_rate_unanswerable`, not only accuracy.

## Statistical honesty on a small set

Twelve questions is not a benchmark. With 12 items, one question is 8 percentage points,
so a difference of one question is not a difference. Report:

- the count, not only the rate (`9 of 12`);
- the absolute change and how many questions moved;
- which questions changed, by id.

Do not compute a confidence interval and pretend it settles a 12-item set. Do not say
"improved" when two questions swapped.

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Accuracy is 1.0 immediately | Questions written from the source text, or `must_contain` copied from the prompt | Rewrite questions in a user's words |
| Metrics change between runs | Non-deterministic client or unpinned model | Record model id and temperature |
| Every item scores as a refusal | Threshold too high, index empty | Inspect one `Answer.as_dict()` |
| Gold document never retrieved | Chunking lost the passage | Search a distinctive phrase directly |
| The report has no failures | `must_contain` too permissive, or the set is too small | Add unanswerable and adversarial items |
| Fine-tuned leg silently absent | Missing checkpoint | Check `finetuned_leg: skipped` in the report |

## Checkpoint

- [ ] You can explain why `hit_at_k` and `answer_accuracy` must be read together.
- [ ] You can name three error categories and how each is detected.
- [ ] You can say what a 12-question set can and cannot support.
- [ ] You can state one metric that would reveal a safety regression.

## Next step

Build [Project G](projects/g-evaluation.md), then read
[CA15 - Integrating fine-tuned models into a chatbot](ca15-fine-tuned-models.md).
