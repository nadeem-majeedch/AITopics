# Project C - A Streamlit conversational application

**Section path:** [Overview](../index.md) · Module [CA06](../ca06-streamlit-interface.md) · **Project C** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 3 hours |
| **Hardware** | CPU-only; needs `requirements/llm.txt` |
| **Code** | `projects/chatbots-rag/app_streamlit.py` |
| **Prerequisite** | CA06 |

## The task

Build a chat interface that shows the answer, its sources, and its refusals, with controls
for `k` and the refusal threshold. The interface must contain no retrieval or prompt logic.

## Run the reference implementation

```bash
python -m pip install -r requirements/llm.txt
python scripts/make_chatbot_data.py
python -m streamlit run projects/chatbots-rag/app_streamlit.py
```

!!! warning "Verified status"
    In the authoring environment this file was **syntax-checked only**
    (`python -m py_compile projects/chatbots-rag/app_streamlit.py` succeeded). Streamlit
    was not installed, so the browser behaviour is unverified. Record in your README
    whether you ran it, and with which Streamlit version.

## What to submit

```text
ca-project-c/
  README.md            # how to run, Streamlit version, what you verified
  app.py               # your interface
  screenshot.png       # a real session showing an answer with sources
  refusal.png          # a real session showing a refusal
  test_cases.md        # manual UI cases and results
  reflection.md        # 200-300 words
```

Two screenshots, because the refusal state is the one students forget to build and the one
that matters most.

## Steps

1. **Initialise session state** for messages and the bot; do not recreate the index on
   every message.
2. **Cache the index** with `@st.cache_resource`, keyed on corpus, `k`, and `min_score`.
3. **Render three outcomes**: grounded answer with sources, refusal with "no sources",
   conflict with a warning.
4. **Add a sources expander** showing number, title, section, path, and score.
5. **Add a debug expander** with `answer.as_dict()`.
6. **Add sidebar controls** for `k`, `min_score`, corpus path, and a rebuild button.
7. **Test the UI manually** and record each case in `test_cases.md`.

## Expected behaviour

| Interaction | Expected |
| --- | --- |
| Ask a supported question | Answer plus sources panel |
| Ask an unsupported question | Refusal plus "no sources cited" |
| Set `min_score` to 0.9 | Most questions refuse |
| Set `min_score` to 0.0 | Answers appear more often, including weaker ones |
| Change `k` | Number of sources changes |
| Rebuild index | History and cache clear |
| Second message | History is retained, and the first turn is still visible |

## Test cases to include

| # | Case | Pass condition |
| --- | --- | --- |
| 1 | Supported question | Answer + at least one source with a section name |
| 2 | Unsupported question | Refusal, no sources, no invented claim |
| 3 | `min_score` raised | Refusal rate visibly increases |
| 4 | Missing corpus path | Clear error with the generator command |
| 5 | Rebuild | Conversation cleared, no stale sources |
| 6 | Two consecutive messages | Both visible; second has context |

## Constraints

- No logic in the UI beyond calling the pipeline and rendering the result.
- No documents sent anywhere; the offline client is the default.
- No personal data in screenshots: redact paths, usernames, and any real document text.
- Do not commit `outputs/` or `.streamlit/secrets.toml`.

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Interface honesty | 30 | Sources, refusals, and conflicts all visible and distinguishable | Only the answer is shown |
| Separation of concerns | 25 | UI contains no retrieval or prompt code | Pipeline logic embedded in callbacks |
| State handling | 20 | Index cached, conversation isolated per session | Rebuild on every rerun |
| Verification | 15 | Both screenshots plus a manual test table | Screenshot of a happy path only |
| Documentation | 10 | README reproduces the run in two commands | Undocumented dependencies |

## Extension tasks

1. Add a **"why did you refuse?"** panel that shows `top_score`, `retrieved`, and the
   `min_score` in effect, so a user can understand a refusal.
2. Add **feedback buttons** that write only a boolean and a hashed session id — no text —
   and explain in your README why you chose not to log the message.
3. Add a **corpus switcher** between `corpus/` and `adversarial/` and demonstrate the
   withheld-evidence notice.

Next: [Project D](d-local-model.md).
