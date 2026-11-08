# Project E - A chatbot that answers questions about course documents

**Section path:** [Overview](../index.md) · Modules [CA09](../ca09-embeddings.md), [CA10](../ca10-chunking.md), [CA11](../ca11-vector-search.md) · **Project E** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 12% of the section assessment |
| **Time** | 4 hours |
| **Hardware** | CPU-only |
| **Code** | `projects/chatbots-rag/project_e_course_docs_bot.py` |
| **Prerequisite** | CA09-CA11 |

## The task

Point the pipeline at a real document collection — the course's own `docs/` tree — and
measure what changes when the corpus is large, cross-referenced, and written for humans
rather than for retrieval.

Then do it again on documents you choose, and compare chunking policies.

## Run the reference implementation

```bash
cd projects/chatbots-rag
python project_e_course_docs_bot.py --index-stats
python project_e_course_docs_bot.py "What weight does the independent lab carry?"
```

`--index-stats` prints documents, chunks, and chunk-size statistics. Run it before asking
questions: if the answer is not in the index, no prompt will find it.

## What to submit

```text
ca-project-e/
  README.md            # corpus, licence, chunking policy, commands
  docs_bot.py          # your implementation
  index_stats.md       # documents, chunks, size distribution
  chunking_compare.md  # two policies, measured on the same questions
  test_cases.md        # ten questions with results and error categories
  reflection.md        # 200-300 words
```

## Steps

1. **Index `docs/`** and record documents, chunks, and the size distribution.
2. **Ask five questions you know the answer to**, and check the cited file by opening it.
3. **Ask five questions the corpus cannot answer** and confirm refusal.
4. **Run a second chunking policy** (`max_chars` 400 with 60 overlap, say) and score both
   on the same ten questions using `hit_at_k`.
5. **Record which policy wins and on which questions**, not only the totals.
6. **Switch to a corpus you choose**, with a licence you can cite, and repeat steps 1-3.

## Expected behaviour

| Case | Expected |
| --- | --- |
| A question whose answer is one sentence | Answer with a citation to that section |
| A question spanning two pages | Either a partial answer with one citation, or a refusal — both acceptable, but record which |
| A question about a page that exists but does not answer it | Refusal, or an answer that cites the wrong page — this is the interesting failure |
| An off-topic question | Refusal |
| After changing chunk size | Different `hit_at_k`; numbers move, so record before and after |

## Test cases to include

| # | Case | Pass condition |
| --- | --- | --- |
| 1 | Known-answer question | Cited file contains the stated fact (you opened it) |
| 2 | Section-title question | The section's own chunk is retrieved (this is the CA10 bug) |
| 3 | Off-topic question | Refusal |
| 4 | Duplicate-content question | Not two near-identical citations |
| 5 | Chunking policy A vs B | A measured comparison, not an opinion |

## Constraints

- Do not index documents you do not have the right to use; record the licence.
- Do not index personal data. The course `docs/` tree contains none.
- Do not change the question set between the two chunking runs.
- Report the exact `max_chars`, `overlap`, and `k` for every number you report.

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Retrieval work | 30 | Two policies measured on identical questions, with diagnosis | One policy, no comparison |
| Evidence | 25 | Every claimed answer verified by opening the cited file | Answers accepted because they look right |
| Failure analysis | 20 | Wrong-page and refusal cases explained | Only successes reported |
| Licensing | 15 | Corpus licence and provenance documented | Unstated source |
| Reproducibility | 10 | Commands and settings recorded | Missing parameters |

## Extension tasks

1. **Add a title-only index** (index titles and headings, not bodies) and measure whether
   it helps section-title questions without hurting body questions.
2. **Deduplicate** near-identical chunks and report the effect on citation precision.
3. **Add BM25-only as a third policy** and check whether the ranking of policies changes.

Next: [Project F](f-cited-assistant.md).
