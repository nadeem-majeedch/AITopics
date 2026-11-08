# Project H - A final domain-specific assistant

**Section path:** [Overview](../index.md) · Module [CA16](../ca16-privacy-and-deployment.md) · **Project H** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 15% of the section assessment |
| **Time** | 6 hours |
| **Hardware** | CPU-only (GPU or API optional) |
| **Code** | `projects/chatbots-rag/project_h_domain_assistant.py` |
| **Prerequisite** | CA13, CA14, CA16 |

## The task

Assemble everything into one assistant for a domain you choose: your own documents (with
permission) or a synthetic corpus you generate. It must retrieve, cite, refuse, log
minimally, and come with an evaluation you ran and a stated limitation you found.

This is the section's capstone. The code is the smallest part of it.

## Run the reference implementation

```bash
cd projects/chatbots-rag
python project_h_domain_assistant.py --selftest
python project_h_domain_assistant.py --checklist
python project_h_domain_assistant.py --ask "What should a chatbot log?"
```

Verified output:

```text
PASS  in-domain question answered with a citation
PASS  out-of-domain question refused
PASS  conversation history retained for follow-ups
PASS  empty question rejected
0 failure(s)
```

## What to submit

```text
ca-project-h/
  README.md            # purpose, users, how to run, what it does not do
  assistant.py         # your implementation
  corpus/              # your documents, or the generator you used
  corpus_card.md       # source, licence, size, personal-data statement
  evaluation.md        # question set, metrics, error table
  model_card.md        # intended use, limits, measured performance
  risk_note.md         # privacy, access control, misuse, rollback
  reflection.md        # 300-400 words
```

## Steps

1. **Write the scope** in five sentences: users, questions, source, refusal policy, cost of
   a wrong answer. (CA01's five questions.)
2. **Assemble the corpus** and write `corpus_card.md` with source and licence.
3. **Index and ask ten questions** you can verify by opening the source.
4. **Write 20 evaluation questions** including 4 unanswerable and 1 adversarial document.
5. **Run the harness** and classify every failure.
6. **Add minimal logging** and verify a log record contains no raw text.
7. **Write `model_card.md`** with measured numbers and at least one limitation you found
   yourself.
8. **Run the checklist** and fix what fails.

## Expected behaviour

| Scenario | Expected |
| --- | --- |
| In-domain question | Answer with resolvable citation |
| Out-of-domain question | Refusal naming the domain |
| Question about a document the user cannot see | Refusal, and no paraphrase of its content |
| Follow-up question | Answered with history, or a clarification request |
| Adversarial document | Quarantined, payload absent from the answer |
| Log inspection | Counts and hashes only, no user text |

## Test cases to include

| # | Case | Pass condition |
| --- | --- | --- |
| 1 | In-domain | Citation resolves to a real chunk |
| 2 | Out-of-domain | Refusal, no invented answer |
| 3 | Follow-up | History used; no contradiction |
| 4 | Permission boundary | Forbidden document never cited or paraphrased |
| 5 | Injection document | Payload absent from answer |
| 6 | Log check | No raw text in any record |
| 7 | Checklist | All nine items answered honestly |

## Constraints

- Documents you have the right to use, with the licence recorded.
- No personal data unless the owner consented and you can explain the retention.
- No secrets in the repository; `.env` stays out of Git.
- Do not claim production readiness. State what you measured and what you did not.
- Do not present a synthetic corpus as real institutional data.

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Scope and design | 20 | Clear users, sources, refusal boundary, non-goals | "Ask it anything about the topic" |
| Grounding and refusal | 25 | Citations resolve; refusals on unsupported questions | Answers without sources |
| Evaluation | 25 | 20 questions, metrics, diagnosed failures | A demo with no numbers |
| Privacy and risk | 20 | Minimal logs, permission filtering, rollback, honest risks | Logging everything, no risk note |
| Communication | 10 | Reader can rerun and understand limits | Undocumented, overclaimed |

## Extension tasks

1. **Add per-user permissions** to retrieval and demonstrate a two-user test where one user
   cannot retrieve the other's document.
2. **Add a second corpus** (a different handbook) and measure whether your `min_score` and
   `k` transfer. They usually do not; report the new values.
3. **Add feedback capture** that stores a boolean and a hashed session id only, then write
   two paragraphs explaining what you can and cannot learn from it.

Next: score the whole section with the [assessment](../assessment.md).
