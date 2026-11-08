# P02 - Domain-specific text classifier

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Foundation |
| **Effort** | 30-40 hours |
| **Hardware** | CPU-only; the default dataset trains in seconds |
| **Prerequisites** | [F04 cleaning](../../lessons/f04-data-cleaning/index.md), [F05 splits](../../lessons/f05-splits/index.md), [F08 classification](../../lessons/f08-regression-classification/index.md), [F10 metrics](../../lessons/f10-metrics-validation/index.md), [CA09 embeddings](../../lessons/chatbots-rag/ca09-embeddings.md), [CA14 evaluation](../../lessons/chatbots-rag/ca14-evaluation.md) |
| **Builds on** | The retrieval and evaluation habits of the Conversational AI section |

## 1. Problem statement and motivation

A support inbox receives free-text messages that must be routed to the right team
(billing, delivery, refunds, account access, technical). Routing by hand is slow
and inconsistent. A classifier can suggest a queue and a confidence; a human still
routes anything uncertain.

The interesting part is not "train a classifier". It is that text classifiers are
easy to evaluate dishonestly: near-duplicate messages, template phrasing, and
class-correlated vocabulary all inflate scores. This project makes you measure
that inflation and choose a model you can defend.

**Decision supported:** which queue a message is suggested for, and when to send
it to a human instead.

## 2. Intended learning outcomes

1. Build a text preprocessing pipeline and justify each step (or justify skipping it).
2. Train at least three model families: a keyword/rule baseline, TF-IDF with a
   linear model, and one embedding-based or neural approach.
3. Detect and measure template leakage with a grouped split, and quantify the
   difference against a random split.
4. Report macro-averaged metrics with per-class breakdowns and a confusion matrix.
5. Calibrate confidence and implement an abstention rule with a measured coverage
   and accuracy trade-off.
6. Analyse errors by length, class, and vocabulary overlap, not by anecdote alone.
7. Document dataset provenance and the limits of a synthetic corpus.

## 3. Difficulty and prerequisites

**Level:** Foundation, with one genuinely hard idea (leakage through phrasing).
30-40 hours: 5 data, 8 modelling, 10 evaluation, 7 abstention and error analysis,
10 writing.

Requires F04, F05, F08, F10. CA09 and CA14 help if you use embeddings. You do not
need a GPU; if you reach for a transformer, use a small one and expect CPU minutes
per epoch.

## 4. Scope and out-of-scope features

**In scope**

- Five-class routing on short English messages.
- Rule baseline, TF-IDF + linear model, and one further model of your choice.
- Grouped split plus an explicit random-split comparison to show the inflation.
- Abstention with measured coverage/accuracy trade-off.
- A CLI that classifies one message or a CSV and writes predictions with confidence.

**Out of scope**

- Multi-label routing (a message can plausibly have two queues; you must pick one
  and say why).
- Languages other than the one in your dataset. Multilingual claims require
  multilingual evaluation.
- Generative replies. This project classifies; P04 generates.
- Production serving, authentication, or a web UI beyond a minimal CLI.

## 5. Dataset options, licences, and preparation

| Option | Source | Licence | Notes |
| --- | --- | --- | --- |
| A (default, offline) | `python scripts/make_capstone_data.py` → `data/capstones/tickets/` | CC0-1.0 | 480 synthetic tickets, 5 intents, 40 templates. Splits are grouped by template. |
| B | UCI SMS Spam Collection | CC BY 4.0 per the UCI dataset page | Binary spam/ham. Re-frame the task honestly; you lose the five-class routing story. |
| C | Your own organisation's tickets | Requires written permission and a privacy review | Remove names, addresses, card numbers, and anything identifying before training. Do not commit the data. |

**Preparation (option A)**

1. Generate and verify: `python scripts/make_capstone_data.py` then
   `--check`. Record the manifest hash.
2. Read `data/capstones/tickets/dataset_card.md`. It lists the known weakness:
   template-generated language.
3. Inspect `leakage.json`: 25 train templates, 5 validation, 10 test, zero overlap.
4. Load with pandas, confirm five labels and no empty texts. Report class counts
   per split.
5. Build a random split of the same rows (for the leakage experiment only). Keep
   it clearly separate from the honest split.

**Measured baselines on option A** (scikit-learn defaults, seed fixed, test split
of 120 rows, class balance 24 each). These are measurements from this repository,
not targets:

| Model | Test accuracy | Test macro F1 |
| --- | --- | --- |
| Majority class | 0.200 | 0.067 |
| TF-IDF word 1-2 grams + logistic regression | 0.683 | 0.691 |
| TF-IDF character 3-5 grams + logistic regression | 0.833 | 0.835 |

The character model wins because the corpus repeats phrasing across variants. That
is a property of the data, not evidence that character n-grams are better for
support tickets. Say so in your report.

## 6. Recommended baseline

**Keyword rules.** One list of terms per class, first match wins, everything else
goes to a fallback. Report its accuracy and macro F1 and how many messages fall
through. This baseline is what a non-ML engineer would ship in a day, and it is
often surprisingly strong on templated text.

Then TF-IDF + logistic regression as the first learned model. Report both, plus a
confusion matrix for the learned model.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Data audit and both splits | Class counts, leakage report, random-split construction | 5 |
| 2 | Rule and linear baselines | Metrics table, confusion matrix | 8 |
| 3 | Third model | Embedding or neural model, same split, tuning on validation only | 8 |
| 4 | Leakage experiment | Random vs grouped scores side by side, per-class effect | 5 |
| 5 | Abstention | Coverage/accuracy curve, chosen threshold, reason | 5 |
| 6 | Error analysis and package | Error taxonomy with counts, report, model card, clean rerun | 9 |

## 8. Repository or folder structure

```text
capstone-p02/
  README.md
  requirements.txt
  data/
    dataset-card.md
    prepare.md
  src/
    prepare.py        # load, validate, write grouped and random splits
    rules.py          # keyword baseline
    train.py          # TF-IDF + linear, third model, saves model + metrics
    evaluate.py       # metrics, confusion, per-class, abstention curve
    predict.py        # CLI: --text or --csv
  tests/
    test_rules.py
    test_prepare.py
    test_predict.py
  reports/
    report.md
    model-card.md
    error-analysis.md
  outputs/
    metrics.json
    predictions_test.csv
```

## 9. Detailed development tasks

1. `prepare.py`: validate schema, strip whitespace, reject empty text, write
   `splits_grouped.json` and `splits_random.json` with row ids. Never split by row
   when a template id exists.
2. `rules.py`: keyword lists with priority order. Log unmatched messages so you can
   report coverage.
3. `train.py`: TF-IDF (word) + logistic regression with `class_weight="balanced"`.
   Save the vectoriser and model with `joblib`, plus the label order.
4. Add a character n-gram variant. Compare it honestly; explain the difference in
   terms of the data, not in terms of fashion.
5. Third model: either (a) sentence embeddings from a small local model with a
   linear head, or (b) a small trained classifier on top of hashed features. State
   the compute cost.
6. Leakage experiment: train the best pipeline on the random split and on the
   grouped split. Report both test scores, and per-class changes. If there is no
   gap, investigate rather than concluding leakage is impossible.
7. Abstention: use predicted probability below a threshold τ. Sweep τ from 0.05 to
   0.95 and plot (as a table) coverage versus accuracy on the covered subset. Choose
   τ from a routing-cost argument: what does a misroute cost versus a manual review?
8. Error analysis: 30 misclassified test messages, tagged by cause (ambiguous
   intent, shared vocabulary, too short, template phrasing unseen, label noise).
   Report counts per cause and two examples per cause.
9. `predict.py`: `--text "..."` prints label, confidence, and "route to human"
   when below τ. `--csv in.csv --out out.csv` writes one row per input.
10. Tests: rules return a label for every input; predict handles empty and very
    long strings; the saved model reloads and reproduces the stored metrics.
11. Model card: intended use, classes, metrics with macro averages, abstention
    behaviour, known failure classes, prohibited uses (no automatic account
    action, no sentiment inference about a person).

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| Schema test | Bad rows are rejected | Empty text raises; unknown label raises |
| Split test | Grouped split has no template overlap | Set intersection empty |
| Rule test | Baseline is deterministic | Same input, same label, twice |
| Round-trip test | Saved model reloads | Metrics match `metrics.json` within 1e-9 |
| Abstention test | Threshold is applied | Inputs below τ are flagged, not silently labelled |
| CLI test | Tool works outside a notebook | `predict.py --text` prints a label and exits 0 |

Protocol: choose the model and τ on validation; touch test once for the final
numbers. The random-split run is reported as an experiment, not as a result.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| Macro F1 | Every class matters equally for routing |
| Per-class precision and recall | A rare urgent class must not be sacrificed |
| Confusion matrix (counts) | Shows which queues get merged |
| Coverage and accuracy at τ | The human-review budget is the real constraint |
| Expected calibration error | Confidence is displayed to a human |
| Inference latency per message (median, p95) | Routing is interactive |

**Qualitative**

- Error taxonomy with counts, not a list of anecdotes.
- Whether the label set itself is coherent: two classes that mean the same thing
  will always confuse the model, and that is a data problem.
- A statement that the corpus is synthetic and repetition inflates scores.

## 12. Expected deliverables

- [ ] README with a one-command rerun and the exact commands used.
- [ ] Dataset card and manifest hash.
- [ ] Four models measured: majority, rules, word TF-IDF, char TF-IDF, plus your
      third model (five rows total).
- [ ] Leakage experiment table: random versus grouped split.
- [ ] Abstention table and chosen τ with justification.
- [ ] Error analysis with counts and examples.
- [ ] Model card.
- [ ] Tests passing.
- [ ] Reflection.

## 13. Suggested extensions

- Add a "none of the above" class using messages that fit no queue, and measure how
  often the model is confidently wrong on them.
- Replace the argmax with a cost-sensitive decision rule where misrouting a refund
  costs more than misrouting a delivery question.
- Compare a frozen embedding model against TF-IDF at equal latency budget.
- Build a small active-learning loop: rank unlabelled messages by uncertainty and
  label 20 by hand, then measure the change.

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Test accuracy 1.0 | Random split on templated text | Use the grouped split; report the gap |
| Character model much better than word model | Repeated phrasing | Report it as a dataset property; try a paraphrase test set |
| One class never predicted | Class imbalance or overlapping vocabulary | Check per-class recall; use class weights; inspect the confusion matrix |
| Confidence high on wrong predictions | Uncalibrated linear model | Calibrate on validation; report ECE; abstain |
| Abstention helps accuracy but coverage collapses | τ too high | Plot the whole curve and choose from cost, not from the best point |
| `predict.py` works in notebook only | Relative paths | Resolve paths from the file location; test from another directory |
| Non-ASCII text crashes the CLI | Console encoding | Write UTF-8 explicitly; escape control characters in output |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Problem framing and label design | 10% | Classes are coherent, decision and abstention are motivated | Classes and decision stated | Labels vague or overlapping | No clear task |
| Data handling and leakage control | 20% | Grouped split, quantified leakage gap, provenance documented | Grouped split with audit | Random split only, or audit incomplete | Leakage unexamined |
| Model comparison | 20% | Rules, linear, and a third model compared fairly with costs | Three models compared | Two models, unfair comparison | One model, no baseline |
| Evaluation and error analysis | 25% | Macro and per-class metrics, calibration, abstention curve, error taxonomy with counts | Correct metrics and some analysis | Metrics only | Misleading or absent |
| Reproducibility and code quality | 15% | One-command rerun, tests, clean CLI | Reruns with minor steps | Manual steps undocumented | Cannot rerun |
| Communication and limitations | 10% | Synthetic-data limits stated precisely; model card complete | Limitations stated | Thin limitations | Claims exceed evidence |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 core met, weak evidence;
below 70 revisit leakage and evaluation.

## 16. Self-review checklist

- [ ] The grouped split has zero template overlap, and I checked the file.
- [ ] The random-split number is reported as a leakage demonstration.
- [ ] Macro F1 is reported with per-class precision and recall.
- [ ] The abstention threshold comes from a cost argument.
- [ ] Calibration is measured, not assumed.
- [ ] At least 30 errors are categorised with counts.
- [ ] The model card names prohibited uses.
- [ ] Tests pass from a clean checkout with generated data.
- [ ] No real customer text, names, or secrets are committed.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Label taxonomy** - the five queues, with one example each and the boundary
   cases you had to decide.
2. **Leakage experiment** - random versus grouped split, overall and per class.
3. **Abstention economics** - the cost table behind τ.
4. **Error taxonomy** - cause, count, two examples, proposed fix.

## 18. Demonstration and presentation checklist

- [ ] Classify three live messages: one easy, one ambiguous, one below τ.
- [ ] Show the confusion matrix and name the worst confusion.
- [ ] Show the leakage gap and explain why the grouped number is the honest one.
- [ ] Show the abstention table and the chosen threshold.
- [ ] State one thing the classifier cannot do and one prohibited use.
- [ ] Answer: "A manager wants 99% routing accuracy. What do you tell them?"

**Demo trap:** presenting the character n-gram score as a modelling insight when it
is a dataset artefact. Say which it is.

---

**Previous:** [P01 tabular prediction](p01-tabular-prediction.md) · **Next:** [P03 LoRA fine-tuning](p03-lora-finetune.md) · [Index](index.md)
