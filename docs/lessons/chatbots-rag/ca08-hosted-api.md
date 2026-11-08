# CA08 - Building a chatbot with a hosted model API (optional) {#ca08}

**Section path:** [Overview](index.md) · **Module 8** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 2 hours: 1 h reading, 1 h optional comparison |
| **Hardware** | CPU-only; requires a key **only if you choose this path** |
| **Prerequisites** | CA03, CA05, CA07 |
| **You will produce** | A comparison note, or a written statement that you skipped this module |

## Why this module exists

Hosted models are stronger than anything you can run on a laptop, and using one is a
legitimate engineering choice. It is also a data-processing decision, a cost decision,
and a dependency decision. Students who reach for an API first learn the pipeline as a
black box; students who reach for it *after* building the local path can compare two
things they understand.

Nothing in this section requires this module. If you have no key, skip it and say so in
your reflection. That is a complete answer.

## The three decisions an API call makes for you

| Decision | Local default | What the API changes |
| --- | --- | --- |
| Where the text goes | Your machine | A third party's servers |
| What it costs | Electricity | Per token, metered |
| Which model version runs | Pinned weights | Whatever the provider serves today |

The third one is the quiet one. A provider can update a model and your evaluation
numbers move without your code changing. Record the model name **and** the date of the
run, or your comparison is not reproducible.

## Consent is a constructor argument

```python
class HostedAPIClient:
    def __init__(self, ..., consent_to_send: bool = False):
        if not consent_to_send:
            raise PermissionError(
                "HostedAPI is opt-in: pass consent_to_send=True only after confirming "
                "you may send this document text to a third party."
            )
```

and the CLI exposes it as a flag:

```bash
python project_b_llm_chatbot.py --backend api --consent "your question"
```

Why a constructor guard rather than a comment in the README? Because a comment does not
stop a script, and because the phrase "send this document text to a third party" is the
decision, stated where a developer will read it.

Before enabling it, answer three questions:

1. **Do I have the right to send these documents?** If they contain another person's
   data, consent is not yours to give.
2. **What does the provider retain, and for how long?** Read the current terms, not a
   blog summary.
3. **Is the question answerable locally at acceptable quality?** If yes, the API buys
   nothing.

## Secrets handling

The key comes from the environment, never from code:

```python
self.api_key = os.environ.get(api_key_env)
if not self.api_key:
    raise RuntimeError(f"environment variable {api_key_env} is not set ...")
```

`.env.example` lists the variable names with empty values:

```text
CHATBOT_BACKEND=fake
CHATBOT_API_KEY=
CHATBOT_BASE_URL=https://api.openai.com/v1
CHATBOT_MODEL=
```

`.gitignore` excludes `.env` and allows `.env.example` to be committed. Four habits:

- never paste a key into a notebook, a screenshot, or a chat message;
- never log the request headers;
- rotate a key that has appeared anywhere public;
- keep the key out of the browser entirely — a client-side key is a published key.

## What to compare, and how

A useful comparison holds everything constant except the model. Same corpus, same `k`,
same prompt, same question set:

```bash
python project_g_evaluation.py --split test --out outputs/eval_local.json
# switch the client in project_g_evaluation.py to the hosted backend, then
python project_g_evaluation.py --split test --out outputs/eval_hosted.json
```

Report, in one table:

| Metric | Local | Hosted |
| --- | --- | --- |
| `answer_accuracy` | measured | measured |
| `abstention_correct` | measured | measured |
| `citation_precision` | measured | measured |
| `mean_latency_ms` | measured | measured |
| Model id and date | recorded | recorded |

Two rules for honesty:

- **Do not compare runs with different prompts or `k`.** That is a different experiment.
- **Do not report "better" without the same question set.** If the hosted model improves
  accuracy on your set, say by how much, on how many questions, and which ones changed.

## Errors specific to remote calls

| Error | Meaning | Handling |
| --- | --- | --- |
| `HTTP 401` | Bad or missing key | Fix the key; do not retry |
| `HTTP 403` | Model or region not permitted | Change model or stop |
| `HTTP 429` | Rate limited | Backoff with a cap; surface the wait |
| `HTTP 5xx` | Provider fault | Retry once, then fail clearly |
| Timeout | Slow response | Bound the timeout; a hang is worse than a refusal |
| Empty completion | Filter or stop sequence | Treat as refusal |

Retries must be bounded and logged. An unbounded retry loop against a metered endpoint
turns an outage into a bill.

## Cost awareness

Estimate before you run a 200-question evaluation: prompt tokens (system prompt plus
evidence) plus completion tokens, multiplied by questions, at the provider's current
price. A rough calculation for a 14-question dev set is trivial; a 500-question
benchmark is not. Write the estimate in your report, then the actual.

## Privacy checklist before the first call

- [ ] The corpus contains no personal data, or its owner consented.
- [ ] The provider's retention terms are acceptable for this data.
- [ ] The key is in the environment, not in the repository.
- [ ] Logging stores counts and hashes, not raw text.
- [ ] The report states which model was used and when.

If any box is unchecked, the correct action is to stay on the local path. That is not a
lesser outcome; it is the design this section is built around.

## Checkpoint

- [ ] You can explain why the API client requires explicit consent.
- [ ] You can name three things an API call decides for you.
- [ ] You can describe a fair comparison protocol between local and hosted.
- [ ] You can state what you personally verified, if you used a key at all.

## Next step

Read [CA09 - Embeddings and semantic similarity](ca09-embeddings.md). From here the
section becomes about retrieval, where most chatbot quality is won or lost.
