# Project B - A simple LLM chatbot in Python

**Section path:** [Overview](../index.md) · Modules [CA03](../ca03-calling-a-model.md), [CA04](../ca04-history-and-context.md), [CA05](../ca05-prompts-and-structured-output.md) · **Project B** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only |
| **Code** | `projects/chatbots-rag/project_b_llm_chatbot.py` |
| **Prerequisite** | CA03-CA05 |

## The task

Build a chat loop with one model interface, a system prompt with an explicit refusal rule,
bounded history that reports what it dropped, and a structured output contract with a
parser that fails closed.

It must run with no account and no download, and swap to a real backend without changing
the chatbot code.

## Run the reference implementation

```bash
cd projects/chatbots-rag
python project_b_llm_chatbot.py --selftest
python project_b_llm_chatbot.py "What is a context window?"
```

Verified output:

```text
backend: fake-extractive-v1
turn 1: I do not have enough evidence in the provided documents to answer that.
PASS  refused without evidence
PASS  rejected empty message
PASS  history bounded (dropped 10 turns)
0 failure(s)
```

The refusal is correct: this project supplies no evidence, and a model with no evidence
must not answer from memory. That behaviour is the point, and it is what you will test.

## What to submit

```text
ca-project-b/
  README.md            # backends used, how to run, what is verified
  chat_bot.py          # your implementation
  prompts.md           # your system prompt and why each rule exists
  test_cases.md        # table of cases and results
  transcript.txt       # a real session, including a refusal and a trimmed history
  reflection.md        # 200-300 words
```

## Steps

1. **Define the client interface** in one place: `name` and `complete(messages)`.
2. **Write the system prompt**: role, scope, refusal rule, output format. Explain each
   rule in `prompts.md`.
3. **Implement a session**: history, a turn counter, and a cap on turns and characters.
4. **Make trimming visible**: increment a dropped counter and add a summary note.
5. **Parse the reply**: if it is JSON with an `answer` field, show the answer; if it is
   malformed, refuse.
6. **Test five cases** including a refusal, an empty message, and a long conversation that
   forces trimming.
7. **Swap the backend once** (`--backend local`) and record what changed — including that
   nothing in your session code did.

## Expected behaviour

| Case | Expected | Why |
| --- | --- | --- |
| Question with no evidence available | Refusal | No grounding source |
| Empty or whitespace message | `ValueError` | Input contract |
| Conversation longer than `max_turns` | Earlier turns dropped, summary note present | Bounded context |
| Malformed model reply | Refusal | Fail closed |
| Same question twice | Same answer with temperature 0 on the offline client | Determinism check |

## Test cases to include

| # | Case | Pass condition |
| --- | --- | --- |
| 1 | In-scope question with a supplied evidence block | Answer cites the block |
| 2 | Question with no evidence | Refusal, no invented text |
| 3 | Empty input | Raises |
| 4 | 10-turn conversation with `max_turns=4` | `dropped_turns > 0`, summary note present |
| 5 | Reply that is prose, not JSON | Refusal, no exception |

## Constraints

- The offline path must run with no key, no download, and no network.
- No secret in code, notebooks, or screenshots.
- Do not claim a model's answer is correct because it is fluent.
- If you use the `api` backend, record the model id and the date, and confirm you may send
  the text.

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Design | 25 | One interface; backends swap without touching session code | Provider calls scattered through the app |
| Prompt quality | 20 | Rules are specific and each is justified | "Be helpful and accurate" |
| State handling | 20 | Trimming explicit and reported | Silent loss, or unbounded growth |
| Failure handling | 20 | Malformed reply and empty input both handled | Crashes or invents |
| Reproducibility | 15 | Two commands rebuild the result | Missing environment details |

## Extension tasks

1. Add **streaming**: yield tokens as they arrive, and make the UI show partial text.
   Keep a non-streaming path for tests.
2. Add a **token estimate** using a simple word-count heuristic, and compare it with the
   character cap. Which is a better predictor of truncation for your corpus?
3. Add a **pinned constraints** slot: extract "the user is asking about campus X" into a
   system-level note that survives trimming. Demonstrate a case that fails without it.

Next: [Project C](c-streamlit-app.md).
