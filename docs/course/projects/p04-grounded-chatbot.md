# P04 - Document-grounded chatbot with citations

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Intermediate |
| **Effort** | 40-50 hours |
| **Hardware** | CPU-only for the default pipeline; a local small model is optional |
| **Prerequisites** | [CA09 embeddings](../../lessons/chatbots-rag/ca09-embeddings.md), [CA10 chunking](../../lessons/chatbots-rag/ca10-chunking.md), [CA11 vector search](../../lessons/chatbots-rag/ca11-vector-search.md), [CA12 RAG](../../lessons/chatbots-rag/ca12-rag.md), [CA13 citations and abstention](../../lessons/chatbots-rag/ca13-citations-and-abstention.md), [CA14 evaluation](../../lessons/chatbots-rag/ca14-evaluation.md), [CA16 privacy](../../lessons/chatbots-rag/ca16-privacy-and-deployment.md) |
| **Builds on** | Projects E, F, and G of the Conversational AI section |

## 1. Problem statement and motivation

People ask questions about a document collection they do not want to read: a
handbook, a policy set, a product manual. A chatbot that answers from its own
memory is untrustworthy; a chatbot that quotes the passage it used can be checked.
Citations turn an answer into a claim with evidence, and evidence is what makes a
retrieval system auditable.

The hard part is not wiring a retriever to a generator. It is measuring whether
the cited passage actually supports the sentence it is attached to, and refusing
when nothing does.

**Decision supported:** whether a user can rely on an answer without opening the
source. If the system cannot show evidence, it must say so.

## 2. Intended learning outcomes

1. Build a chunking strategy with metadata and justify chunk size and overlap with
   measured retrieval quality.
2. Compare at least two retrieval methods (lexical and dense, or dense and hybrid)
   on a labelled question set.
3. Generate answers that cite chunk ids, and verify those ids resolve to real text.
4. Measure faithfulness: does the cited text entail the claim?
5. Implement abstention for unanswerable questions and measure false-answer rate.
6. Test prompt injection through retrieved documents and report what happens.
7. Document corpus provenance, licence, and the retention policy for queries.

## 3. Difficulty and prerequisites

**Level:** Intermediate. 40-50 hours: 8 corpus and chunking, 10 retrieval, 10
generation and citations, 12 evaluation, 10 writing.

Requires CA09-CA14. You should already have built a retrieval index once; this
project asks you to evaluate it rather than to discover it.

## 4. Scope and out-of-scope features

**In scope**

- A corpus of 10-200 documents you have the right to use. The course corpus has 13
  handbook pages plus separate adversarial fixtures; small is fine if you read all
  of it.
- Two retrieval configurations compared on the same labelled questions.
- Answers with inline citations that resolve to a document id and character span.
- Abstention when the best evidence is weak.
- An evaluation harness with retrieval, answer, citation, and refusal metrics.
- A CLI and a minimal local interface (terminal is acceptable; Streamlit optional).

**Out of scope**

- Fine-tuning a generator (that is P03).
- Multi-turn memory beyond a short window. If you add it, it needs its own
  evaluation and it is not required.
- Web search, live crawling, or anything that changes the corpus at query time.
- Handling private user documents without a consent and deletion story.
- Claims of factual accuracy beyond your labelled question set.

## 5. Dataset options, licences, and preparation

| Option | Source | Licence | Notes |
| --- | --- | --- | --- |
| A (default, offline) | `python scripts/make_chatbot_data.py` → `data/chatbots-rag/` | CC0-1.0 | 13-page fictional Study Hub handbook, 14 dev and 12 test questions, adversarial fixtures |
| B | Public documentation you may redistribute | Record the exact licence, for example a project's docs under CC BY 4.0 | Keep the corpus small enough to inspect by hand |
| C | Your own documents | You must own them | Remove personal data; document retention |

**Preparation (option A)**

1. Generate the corpus and verify the manifest.
2. Read the dataset card and at least five documents end to end. You cannot
   evaluate answers about text you have not read.
3. Copy `dev_questions.json` and `test_questions.json`. Use dev for tuning, test
   once at the end. Do not add questions to test after seeing results; if you must,
   log the change and report both versions.
4. Build chunks with metadata: `doc_id`, `title`, `char_start`, `char_end`,
   `heading`. Store them in JSON; a vector database is optional at this scale.
5. Write down your chunking decision and the reasoning before measuring. Then
   measure at least three configurations (for example 200/0, 400/50, 800/100
   characters) and report recall@k for each.

## 6. Recommended baseline

**BM25 or TF-IDF lexical retrieval with extractive answers.** Return the top
passage and quote its most relevant sentence. No generator. This baseline is
fast, deterministic, and often hard to beat on a small corpus. Every generative
answer must be compared against it.

Second baseline: dense retrieval with a small local embedding model. If no model
download is possible, use TF-IDF with character n-grams as the second method and
say so.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Corpus and chunking | Chunk statistics, metadata sample, three chunk configs measured | 8 |
| 2 | Retrieval comparison | Recall@k, MRR, nDCG for two methods | 10 |
| 3 | Grounded generation | Answers with citations, citation-id validity check | 10 |
| 4 | Abstention | Answerable vs unanswerable behaviour, thresholds, false-answer rate | 6 |
| 5 | Faithfulness evaluation | Per-answer support labels, agreement between two raters (you and a checklist) | 8 |
| 6 | Security and package | Injection tests, privacy note, report, rerun | 8 |

## 8. Repository or folder structure

```text
capstone-p04/
  README.md
  requirements.txt
  data/
    corpus/                 # generated or downloaded; not committed if large
    dataset-card.md
    questions/
      dev.json
      test.json
  src/
    build_index.py          # chunk, embed or index lexically, persist
    retrieve.py             # top-k with scores and metadata
    answer.py               # extractive and generative answer paths, citations
    verify.py               # citation resolution and support checks
    evaluate.py             # retrieval, answer, citation, refusal metrics
    cli.py
  tests/
    test_chunking.py
    test_citations.py
    test_refusal.py
  reports/
    report.md
    system-card.md
    annotation-guide.md
  outputs/
    retrieval_metrics.json
    answer_metrics.json
    predictions.jsonl
```

## 9. Detailed development tasks

1. `build_index.py`: deterministic chunking with stable ids (hash of doc id plus
   offsets). Rebuilding twice must produce identical ids.
2. Retrieval: implement lexical scoring (BM25 preferred) from scratch or with a
   small library, and a dense path if you have embeddings. Normalise scores so the
   abstention threshold has meaning.
3. `retrieve.py`: return top-k with `doc_id`, span, score, and the matched terms
   for lexical retrieval. Matched terms make debugging possible.
4. Answer path A (extractive): choose the best sentence from the top chunk using
   term overlap with the question; cite it.
5. Answer path B (generative, optional): prompt a local model with the top 3
   chunks, require citations in a fixed format (`[doc_id:start-end]`), and reject
   any citation that does not resolve. If the model is unavailable offline, say so
   and evaluate the extractive path only.
6. `verify.py`: for every citation, check (a) the span exists, (b) the cited text
   shares at least one content term with the claim, (c) the claim's numbers appear
   in the cited text. These are weak checks; report them as weak.
7. Abstention: if top score is below τ, or the best chunk lacks a content-term
   match, answer "I could not find this in the documents" and cite nothing. Tune τ
   on dev using the cost of a wrong answer versus a refused answer.
8. Evaluate retrieval on test: recall@1, @3, @5, MRR, nDCG@5. Report per-question
   type if your set has types.
9. Evaluate answers: correct / partially correct / incorrect / refused, with a
   written annotation guide and two examples per category. Score a 20-question
   subset twice, a day apart, and report self-agreement. If your agreement is low,
   your labels are unreliable and you must say so.
10. Faithfulness: for each answer, label whether the cited passage supports it
    (supported / partially / not supported / no citation). Report the rate of
    unsupported claims. This is the headline metric.
11. Injection tests: index the adversarial documents, ask a question that retrieves
    them, and record whether the system follows the injected instruction. Report
    the failure; add a mitigation (strip instruction-like text from retrieved
    context, or delimit context explicitly) and re-test.
12. Privacy: state what queries are logged, for how long, and how a user requests
    deletion. If nothing is logged, say that.

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| Chunk id stability | Index is reproducible | Two builds produce identical ids |
| Span validity | Citations point at real text | Every cited span resolves and matches the source |
| Retrieval regression | Changes are measured | Recall@5 does not silently drop on dev |
| Refusal test | Unanswerable questions are refused | At least 80% refused on the unanswerable dev subset, with the rate reported |
| Injection test | Retrieved text cannot steer the system | Behaviour recorded before and after mitigation |
| Determinism | Retrieval is stable | Same query, same top-k, twice |

Protocol: tune on dev, evaluate on test once. Report both retrieval-only and
end-to-end results, because a good retriever with a bad answerer and a bad
retriever with a lucky answerer look identical in an end-to-end average.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| Recall@1, @3, @5 | Did the evidence reach the context window |
| MRR and nDCG@5 | Ranking quality, not just presence |
| Answer correctness rate by category | End-to-end usefulness |
| Unsupported-claim rate | The honesty metric that matters |
| Citation resolution rate | Mechanical validity of citations |
| Refusal rate on unanswerable questions | Measures cowardice and courage separately |
| False-answer rate on unanswerable questions | The dangerous failure |
| Median and p95 latency | Interactive use |

**Qualitative**

- Three answers with citations quoted in full, including one refusal.
- A judgement on whether citations help a reader check the claim in under 30
  seconds.
- Corpus limitations: coverage gaps, stale pages, contradictions between documents.

## 12. Expected deliverables

- [ ] Corpus with a dataset card and licence statement.
- [ ] Chunking rationale plus measurements for three configurations.
- [ ] Retrieval comparison table.
- [ ] Answer predictions with citations for the test set.
- [ ] Annotation guide and labelled answer subset.
- [ ] Faithfulness and refusal results, including failures.
- [ ] Injection test results before and after mitigation.
- [ ] System card and report.
- [ ] Tests passing.

## 13. Suggested extensions

- Add a reranker (cross-encoder or lexical overlap) and measure the latency cost
  against the recall gain.
- Add contradiction detection: two documents disagree, and the system must surface
  both rather than pick one silently.
- Build a "show me the evidence" UI that highlights the cited span in the document.
- Add query rewriting for follow-up questions and measure it separately.

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| High recall, poor answers | Context assembled badly or too much text | Reduce top-k, put the best chunk first, trim boilerplate |
| Citations resolve but do not support the claim | Citation is decorative | Check support, not just resolution; require the claim's numbers in the span |
| Every question answered confidently | No abstention threshold | Add τ and an unanswerable subset |
| Everything refused | τ too high, or scores not normalised | Calibrate on dev; inspect score distributions |
| Injection test succeeds | Retrieved text treated as instructions | Delimit context, strip instruction-like lines, re-test |
| Retrieval changes between runs | Unstable tie-breaking or index rebuild | Sort by score then id; persist the index |
| Numbers in answers are wrong | Generator arithmetic | Require numbers to appear verbatim in the cited span |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Corpus and chunking | 15% | Provenance, three configs measured, metadata used in retrieval | Sound corpus with a measured chunk choice | Chunking unexplained | Corpus unsuitable or unlicensed |
| Retrieval evaluation | 20% | Two methods, multiple k, ranking metrics, error analysis | One comparison with recall@k | Metrics without comparison | No retrieval evaluation |
| Grounding and citations | 25% | Citations resolve and are shown to support claims; unsupported rate reported | Citations resolve; support checked informally | Citations decorative | No citations |
| Abstention and safety | 20% | Refusal tuned with costs, injection tested with mitigation | Refusal implemented and tested | Refusal rules only | No refusal or safety testing |
| Reproducibility | 10% | Deterministic index and retrieval, one-command rerun | Minor manual steps | Undocumented steps | Cannot rerun |
| Communication | 10% | Clear system card, precise limitations | Clear report | Thin | Overstated |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 works, evaluation thin;
below 70 the faithfulness claim is unsupported.

## 16. Self-review checklist

- [ ] Corpus licence and provenance are recorded.
- [ ] Test questions were used once for the final numbers.
- [ ] Every citation resolves to real text.
- [ ] Unsupported-claim rate is reported, not just answer accuracy.
- [ ] Unanswerable questions exist in the test set and refusal is measured.
- [ ] Injection through retrieved text was attempted.
- [ ] Logging and retention are stated.
- [ ] Retrieval and answer quality are reported separately.
- [ ] No personal data is in the corpus or logs.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Corpus and licence** - what is in it, what is missing, who may use it.
2. **Chunking experiment** - the table of configurations and why you chose one.
3. **Retrieval results** - per-method, per-k, with failures quoted.
4. **Faithfulness** - the support labels, the rate, and two unsupported examples.
5. **Safety** - injection test before and after mitigation.

## 18. Demonstration and presentation checklist

- [ ] Ask a question the corpus answers; show the answer and the highlighted span.
- [ ] Ask a question it cannot answer; show the refusal.
- [ ] Ask a question that retrieves an adversarial document; show the behaviour.
- [ ] Show recall@5 and unsupported-claim rate side by side.
- [ ] Explain one retrieval failure and one generation failure.
- [ ] Answer: "How would I know if this answer is wrong?"

**Demo trap:** answering from general knowledge when retrieval fails. The refusal is
the feature.

---

**Previous:** [P03 LoRA fine-tuning](p03-lora-finetune.md) · **Next:** [P05 local assistant](p05-local-assistant-gui.md) · [Index](index.md)
