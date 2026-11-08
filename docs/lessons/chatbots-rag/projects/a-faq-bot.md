# Project A - A rule-based FAQ chatbot

**Section path:** [Overview](../index.md) · Module [CA02](../ca02-chatbot-types.md) · **Project A** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 8% of the section assessment |
| **Time** | 2 hours |
| **Hardware** | CPU-only, standard library |
| **Code** | `projects/chatbots-rag/project_a_faq_bot.py` |
| **Prerequisite** | [CA02](../ca02-chatbot-types.md) |

## The task

Build a deterministic FAQ bot for a bounded domain of your choice: six to ten intents,
explicit priority, an explicit fallback, and a log of ambiguous matches.

The bot must answer every in-scope question correctly and refuse everything else. It must
not guess.

## Run the reference implementation first

```bash
python scripts/make_chatbot_data.py
cd projects/chatbots-rag
python project_a_faq_bot.py --selftest
python project_a_faq_bot.py "can I get my money back"
```

Verified output on the authoring machine:

```text
PASS  'How do I enroll?' -> Enrollment opens on the first Monday of each month and close...
PASS  'can I get a refund?' -> Paid workshop refunds are available within 14 days of purcha...
PASS  'how much does a workshop cost' -> A paid workshop costs 2,500 credits and runs for three sessi...
PASS  'what are the assessment weights' -> A module is scored as knowledge check 20%, guided notebook 3...
PASS  'what is the weather today' -> I only answer questions about enrollment, workshops, labs, a...
PASS  rejection of empty input
Ambiguity check: {'message': 'i want a refund for the workshop i enrolled in', 'intent': 'refund', 'ambiguous': True}
6/6 checks passed
```

## What to submit

```text
ca-project-a/
  README.md          # domain, intents, how to run, what it refuses
  faq_bot.py         # your implementation
  test_cases.md      # table of inputs, expected intents, observed results
  reflection.md      # 200-300 words
```

## Steps

1. **Choose a domain with a closed question set.** Opening hours, a fixed policy, a
   product's specifications. Not "anything about the university".
2. **Write the intent table before the code.** Name, trigger phrases, answer, priority.
3. **Implement normalisation** (lowercase, collapse whitespace) and match on the
   normalised string.
4. **Implement priority**, and log when more than one intent matches.
5. **Implement the fallback** as a real answer that names the domain boundary.
6. **Write ten test cases** including: an exact match, a paraphrase, a two-intent
   message, an out-of-domain question, an empty message, and one that *should* fail.
7. **Run them and record the results honestly**, including any you had to fix.

## Expected behaviour

| Input | Expected |
| --- | --- |
| An exact trigger phrase | The matching intent's answer |
| A paraphrase you anticipated | The matching intent's answer |
| Two intents in one message | The higher-priority intent, with `ambiguous: true` logged |
| An out-of-domain question | The fallback, naming the domain |
| Empty input | `ValueError`, not a fallback |
| A paraphrase you did not anticipate | Falls through — record it, then decide whether to add a rule |

That last row is the lesson. Every rule you add to catch it makes the rule set longer and
the behaviour less general.

## Test cases to include

| # | Case | Pass condition |
| --- | --- | --- |
| 1 | Exact match | Correct intent |
| 2 | Anticipated paraphrase | Correct intent |
| 3 | Two intents | Higher priority wins; ambiguity logged |
| 4 | Out of scope | Fallback, no invented answer |
| 5 | Empty string | Raises, does not answer |
| 6 | Case and whitespace variation | Same intent as the exact match |
| 7 | Unknown phrasing | Recorded as a miss, not silently "fixed" by a broad pattern |

## Constraints

- No model, no network, no third-party package.
- Answers must be facts from a source you can name in `README.md`.
- Do not log personal data; the bot is a demonstration, not a service.
- Do not use a pattern so broad that it catches unrelated questions; a rule that matches
  everything is a fallback in disguise.

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Correctness | 30 | All in-scope cases pass; priority behaviour is deliberate | Passes the happy path, guesses elsewhere |
| Refusal behaviour | 20 | Out-of-scope and empty inputs handled explicitly | Falls back for everything, including valid questions |
| Evaluation | 20 | Ten cases incl. failures, results recorded honestly | Happy-path cases only |
| Reproducibility | 15 | README lets another student rerun in two commands | Missing steps or environment |
| Reflection | 15 | Names a specific phrasing the bot cannot handle and why | Generic "rules are limited" |

## Extension tasks

1. Add a **confidence** field: intents matched by an exact phrase score higher than a
   substring match. Show one case where the score changes the chosen intent.
2. Add **regex-free synonym lists** instead of more patterns, and measure how many of
   your test cases now pass.
3. Write down the point at which you would stop extending the rules and move to
   retrieval. Justify it with a count, not a feeling.

Next: [Project B](b-llm-chatbot.md).
