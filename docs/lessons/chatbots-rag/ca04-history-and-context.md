# CA04 - Conversation history and context windows {#ca04}

**Section path:** [Overview](index.md) · **Module 4** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 3 hours: 1.5 h reading, 1.5 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | CA03 |
| **You will produce** | A conversation with bounded history that reports what it dropped |

## Why this module exists

A context window is a budget, and every part of a chatbot spends from it: the system
prompt, the retrieved documents, the conversation so far, and the answer being
generated. Students usually notice the budget only when a long conversation starts
behaving strangely, and then they guess.

The failure is specific and quiet. A user states a constraint in turn one, the history
is trimmed at turn eight, and the bot answers a follow-up without the constraint — no
error, no warning, just a plausible answer to a slightly different question.

## What a context window is

A **token** is a chunk of text, roughly three-quarters of a word in English. A
**context window** is the maximum number of tokens the model can condition on at once.
Everything you send competes for that space.

| Component | Typical share in this section | Grows with |
| --- | --- | --- |
| System prompt | 100-400 tokens | Prompt complexity |
| Retrieved evidence | 400-1,500 tokens | `k`, chunk size |
| Conversation history | 0-2,000 tokens | Turns, verbosity |
| Answer | 100-800 tokens | Max tokens, style |

A 4,096-token window with `k=4` chunks of 600 characters leaves very little room for
history. Doubling `k` to fix a retrieval miss can silently evict the conversation. That
trade-off is why `k` is a knob in every project here, not a constant.

## Why history helps and how it hurts

History helps with:

- pronouns and ellipsis: "and the second one?" only means something with the first one;
- constraints: language, campus, level, tone;
- corrections: "no, the Lahore campus".

History hurts with:

- **drift**: an early misconception keeps influencing later answers;
- **injection persistence**: once malicious text is in the history, it stays in the
  window across turns;
- **cost and latency**: every turn resends the history;
- **privacy**: history is the most sensitive thing in the system.

The last two are why `logging_safe.py` stores counts and hashes rather than text, and
why the history is capped even when the window allows more.

## The policy, made explicit

`ConversationHistory` is deliberately boring, and every decision is visible:

```python
@dataclass
class ConversationHistory:
    max_turns: int = 8
    max_chars: int = 4000
    turns: list[dict[str, str]] = field(default_factory=list)
    dropped_turns: int = 0
    summarized: str = ""
```

Three behaviours worth studying:

**1. Trimming is reported.** Dropping turns increments `dropped_turns` and keeps a
short tail summary:

```python
def _drop_oldest(self) -> None:
    dropped = self.turns.pop(0)
    self.dropped_turns += 1
    snippet = dropped["content"][:80].replace("\n", " ")
    self.summarized = (self.summarized + f" Earlier: {snippet}").strip()[-240:]
```

**2. The summary is visible to the model as a system note**, not silently merged:

```python
messages.append({
    "role": "system",
    "content": f"Summary of earlier conversation (older turns removed):{self.summarized}",
})
```

A system note says "you are missing context", which is different from pretending the
conversation started at turn seven.

**3. Characters stand in for tokens.** This is an approximation, and the module says so
rather than pretending otherwise. It is accurate enough to demonstrate the failure mode
and it adds no tokenizer dependency. If you know your model's tokenizer, divide by
roughly four words-to-tokens and set `max_chars` from the real budget.

## Observing the failure

```python
from chatbot_core import ConversationHistory

history = ConversationHistory(max_turns=4, max_chars=10_000)
history.add("user", "I am asking about the Lahore campus.")
for i in range(5):
    history.add_exchange(f"question {i}", f"answer {i}")

print(history.dropped_turns)     # > 0
print(history.messages()[0])     # the "older turns removed" system note
```

The first user turn is gone. In a real bot, that is the constraint disappearing.

## Strategies, in order of complexity

| Strategy | What it does | Cost | Risk |
| --- | --- | --- | --- |
| Hard cap on turns | Keep the last N messages | Trivial | Loses old constraints |
| Cap plus summary note | As above, with a visible note | Low | Summary can be wrong |
| Rolling summarisation | Model writes a summary of dropped turns | Medium | Costs a call; can drift |
| Pinned facts | Extract constraints into a small pinned slot | Medium | Needs extraction rules |
| Retrieval over history | Index past turns and retrieve relevant ones | High | Another retriever to evaluate |

Start with the first two. Add summarisation only when you can show, with a test, that
the cap alone loses something that matters.

## History and privacy

History is the highest-risk data in a chatbot because it is verbatim user text. In
this section:

- it is capped, so it cannot grow without bound;
- it is never written to the log by default;
- it is cleared with `bot.reset()`;
- it is not shared between users — one `ConversationHistory` per session.

If you persist history to disk for a feature, you have created a personal-data store.
Module 16 covers what that obliges you to do.

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Follow-up question answered as if standalone | History trimmed, or never passed | Print `len(history)` and the first message before the call |
| Answers drift to an earlier topic | Early turns dominating the window | Inspect the assembled messages, not the final answer |
| Context-length error from a real model | `k` times chunk size exceeds budget | Reduce `k`, then chunk size, then history; in that order |
| The bot repeats the same answer verbatim | History includes the previous answer and the prompt invites copying | Shorten history or restate the question |
| A constraint is honoured once then forgotten | It lives only in a dropped turn | Pin it, or raise `max_turns`, and add a regression test |

## Checkpoint

- [ ] You can name the four consumers of the context window.
- [ ] You can explain why the trimmed-history summary is a system message.
- [ ] You can point to the moment in the code where a turn is dropped.
- [ ] You can state one privacy consequence of persisting history.

## Next step

Read [CA05 - System instructions, prompt templates, structured outputs](ca05-prompts-and-structured-output.md),
then extend [Project B](projects/b-llm-chatbot.md) with a follow-up test.
