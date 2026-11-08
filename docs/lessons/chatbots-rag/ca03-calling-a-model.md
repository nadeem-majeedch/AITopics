# CA03 - Calling a language model from Python {#ca03}

**Section path:** [Overview](index.md) · **Module 3** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h Project B |
| **Hardware** | CPU-only; no download |
| **Prerequisites** | CA02, F01 |
| **You will produce** | A chatbot script with one model interface and three interchangeable backends |

## Why this module exists

Almost every chatbot tutorial starts with a provider SDK. That choice leaks into the
rest of the code: the retry logic knows the provider's error types, the prompt is in
the provider's message format, and swapping models means rewriting the application.

This module does the opposite. It defines one small interface, implements it three
ways, and keeps everything else unaware of which one is running. That is why the
whole section can be tested offline: the offline implementation is just another
client.

## The interface

```python
class ModelClient(Protocol):
    name: str

    def complete(self, messages: Sequence[dict[str, str]], temperature: float = 0.0) -> str:
        ...
```

Three lines of contract, one method. `messages` is a list of `{"role": ..., "content":
...}` dictionaries with roles `system`, `user`, and `assistant` — the shape every chat
model uses, and the shape a prompt template produces.

A client that satisfies this is enough to build everything in Modules 4-14. When you
later add streaming, you add a second method rather than changing the first.

## Three implementations

### The offline client

`FakeModelClient` is an extractive stand-in: it parses the evidence blocks out of the
prompt, scores each sentence by content-word overlap with the question, and returns
the best sentence with the number of the block it came from.

```python
asked = content_words(question)
overlap = asked & content_words(sentence)
scored.append((len(overlap) / len(asked), len(overlap), index, position))
```

It cannot paraphrase, cannot reason, and cannot answer from memory. That is the point:
it is a *test double* whose behaviour you can predict, so a failing test means your
pipeline is wrong rather than the model being moody.

??? note "Why not ship a tiny real model as the default?"
    A 0.5B model is roughly 1 GB to download and needs a transformer stack. Making
    that the default means every student who cannot download it is blocked from
    Module 3, and every test depends on weights that can change. The real model is
    Module 7, where it belongs.

### The local client

```python
from transformers import pipeline
self._pipe = pipeline("text-generation", model=model_id)
```

Loaded lazily, imported only when requested. Module 7 covers the resource realities.

### The hosted client

An OpenAI-compatible HTTP call built on `urllib`, so no SDK is required:

```python
request = urllib.request.Request(
    f"{self.base_url}/chat/completions",
    data=payload,
    headers={"Authorization": f"Bearer {self.api_key}"},
)
```

It refuses to construct without `consent_to_send=True`, and it reads the key from the
environment:

```python
self.api_key = os.environ.get(api_key_env)
if not self.api_key:
    raise RuntimeError(f"environment variable {api_key_env} is not set ...")
```

Two rules that are not negotiable:

- a key is never a code literal, a notebook cell, or a committed file;
- sending document text to a third party is a decision the user makes explicitly.

## Reading a reply: raw text is not a result

Every client returns a string. That string is not yet an answer. Before you can use
it, three things must be true:

| Property | Check |
| --- | --- |
| It is well formed | The reply parses as the structure you requested |
| It is supported | Any cited evidence exists in the retrieved set |
| It is shaped | Length, language, and format are within policy |

Module 5 builds the structured output contract; Module 13 enforces the citation
check. This module establishes the boundary: the model returns *text*, and the
pipeline decides what that text is allowed to mean.

## Errors you will actually hit

| Error | Cause | Handling |
| --- | --- | --- |
| Connection or DNS failure | No network, wrong base URL | Catch, fall back to the offline client, report which client answered |
| `HTTP 401` | Missing or wrong key | Do not retry; the key is wrong |
| `HTTP 429` | Rate limit | Retry with backoff, cap attempts, surface the wait |
| `HTTP 500` | Provider fault | Retry once, then fail with a clear message |
| Timeout | Prompt too long or service slow | Bound the timeout; a hung request is worse than a refusal |
| Empty completion | Prompt or stop sequence consumed the answer | Treat empty as a refusal, never as success |
| Context length exceeded | History plus evidence too large | Trim history (Module 4), reduce `k` (Module 11) |

```python
def safe_complete(client, messages, retries: int = 1):
    for attempt in range(retries + 1):
        try:
            return client.complete(messages)
        except TimeoutError:
            if attempt == retries:
                raise
```

Do not write a bare `except Exception: return "Sorry"`. That turns an outage into a
plausible refusal you will spend an afternoon debugging.

## Temperature and determinism

`temperature=0.0` makes sampling greedy where the backend supports it. It reduces
variation but does not guarantee reproducibility: model versions, tokenisation, and
batching all change results. For evaluation, record the model name and parameters
with every run, and never compare two runs made with different settings as if they
were the same experiment.

## Guided practice

```bash
cd projects/chatbots-rag
python project_b_llm_chatbot.py --selftest
python project_b_llm_chatbot.py --backend fake "What is a context window?"
```

Notice that the offline client refuses: it has no evidence to quote, and it does not
invent. That is the correct behaviour for a memory-less system, and it is the
behaviour you must preserve when you later add a model that *would* happily guess.

## Checkpoint

- [ ] You can write the `ModelClient` interface from memory.
- [ ] You can explain why the offline client is a test double, not a small model.
- [ ] You can name two errors that must not be retried and two that should be.
- [ ] You can explain what `consent_to_send=True` protects against.

## Next step

Read [CA04 - Conversation history and context windows](ca04-history-and-context.md),
then extend [Project B](projects/b-llm-chatbot.md) with bounded history.
