# CA01 - What a chatbot is and how conversational systems work {#ca01}

**Section path:** [Overview](index.md) · **Module 1** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 3 hours: 2 h reading, 1 h exploration |
| **Hardware** | CPU-only |
| **Prerequisites** | F01 (Python) and F02 (environment) |
| **You will produce** | A one-page problem statement for the bot you intend to build |

## Why this module exists

Two students describe their project. The first says: "It is a chatbot that answers
questions about our department handbook." The second says: "It is a retrieval system
over 240 handbook pages that answers questions about deadlines and procedures,
cites the page, and refuses when the handbook is silent."

Only the second can be built, tested, or refused. The difference is not ambition;
it is whether the *task* was specified before the software was chosen.

A chatbot is not a product category. It is an interface that turns text into text
across turns. Everything that makes it useful or useless sits behind that interface:
what it is allowed to know, what it does with a question it cannot answer, and how
anyone would ever check whether it was right.

## What a conversational system actually consists of

| Part | Question it answers | Where it lives in this section |
| --- | --- | --- |
| Input handling | What did the user actually ask? | Module 5 (prompt assembly), Module 13 |
| Knowledge source | Where may the answer come from? | Modules 9-12 (retrieval) |
| Model | How is text produced? | Modules 3, 7, 8 |
| Policy | What must never happen? | Modules 5, 13, 16 |
| State | What was said before? | Module 4 |
| Output contract | What shape is a valid answer? | Module 5 |
| Evidence | Why should anyone believe it? | Module 13 |
| Measurement | How do we know it works? | Module 14 |

A system missing "Evidence" and "Measurement" is a demo. It can still be a good
demo, and Project A is exactly that. The section's job is to add the last two rows
without losing the first six.

### Turns, context, and state

A **turn** is one message from the user plus one reply. A **session** is a sequence
of turns. **State** is whatever the system carries between turns: the history, a
retrieved document set, a chosen language, a user's stated constraint.

State is where naive chatbots break quietly. In turn one the user says "I am asking
about the Lahore campus." In turn six, that constraint has fallen out of the context
window and the answer is about a different campus, with no warning. Module 4 makes
this failure visible and testable.

### Deterministic and probabilistic behaviour

A rule-based bot is deterministic: the same input gives the same output, and you can
list every path. A generative bot is not: sampling, model updates, and context length
all change the output. Determinism is not automatically better — a rule bot cannot
handle "can I get my money back" unless someone anticipated that phrasing — but it is
much easier to test, which is why Project A exists first.

## The three families of chatbot

| Family | How it answers | Strength | Failure mode |
| --- | --- | --- | --- |
| Rule-based | Pattern match to a fixed response | Predictable, auditable, instant | Cannot generalise; unknown phrasing falls through |
| Retrieval-based | Find a passage, return or quote it | Grounded, citable, cheap | Returns a plausible-but-wrong passage |
| Generative | Model writes an answer | Handles open phrasing | Invents facts confidently |

Most useful systems are hybrids: retrieval chooses the evidence, a model writes the
answer, and rules enforce the boundaries. That hybrid is what you build by Module 12.

## The question that decides the design

Before writing code, answer these five questions in writing:

1. **Who is the user, and what decision does the answer support?** "Students
   checking deadlines" is a user. "Anyone curious" is not.
2. **What is the authoritative source?** If the answer is "the model's knowledge",
   you cannot cite, update, or audit it.
3. **What happens when the answer is not in the source?** If the answer is "it
   guesses", stop and choose again.
4. **What does a wrong answer cost?** A wrong restaurant recommendation is annoying;
   a wrong refund deadline is a dispute.
5. **How will you measure it?** If you cannot name ten questions with known correct
   answers, you cannot measure it yet.

## Worked example: scoping the course assistant

A department wants a bot for its student handbook. The first draft scope was "answer
any question about the department". Three questions killed it:

| Question | Why it broke the scope |
| --- | --- |
| "Should I take this course?" | Advice, not handbook content; no authoritative source |
| "Is my fee payment recorded?" | Requires a private system the bot cannot read |
| "What is the deadline for a late withdrawal?" | Answerable, but only from one page that changes yearly |

The revised scope answers only handbook questions about procedures and deadlines,
cites the section, and refuses the other three with an explicit reason. That is a
smaller bot that can be evaluated.

Notice what the revision bought: a testable boundary. "Refuses fee questions" is a
test case. "Answers any question" is not.

## Guided exploration

Run Project A before reading Module 2:

```bash
python scripts/make_chatbot_data.py
cd projects/chatbots-rag
python project_a_faq_bot.py --selftest
python project_a_faq_bot.py "can I get my money back"
```

The last command demonstrates the boundary of the rule-based approach: depending on
whether the author anticipated that phrasing, it either matches the refund intent or
falls through to the fallback. Note which happened, then rewrite a rule to catch it
and observe that you have traded one gap for a longer rule list.

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| "It works but I cannot describe what it does" | No scope statement | Write the five questions above; if you cannot answer #2, the design is not ready |
| Every question gets an answer | No fallback path | Ask an obviously out-of-scope question and see whether it refuses |
| The demo passes but colleagues break it in a minute | Test set came from the author's own phrasings | Collect five questions from someone who has not seen the system |
| Nobody can say if it improved | No fixed question set | Write ten questions with gold answers before the next change |

## Checkpoint

You are ready for Module 2 when you can:

- [ ] State the difference between a turn, a session, and state.
- [ ] Name the three chatbot families and one failure mode of each.
- [ ] Write a scope statement with an explicit refusal boundary.
- [ ] Explain why "the model knows it" is not an evidence source.

## Next step

1. Write your one-page problem statement (user, source, refusal policy, cost of
   error, ten test questions).
2. Read [CA02 - Rule-based, retrieval-based, and generative chatbots](ca02-chatbot-types.md).
3. Build [Project A](projects/a-faq-bot.md).
