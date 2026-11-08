# Conversational AI projects - runnable code

This folder holds the executable half of the
[conversational AI section](../../docs/lessons/chatbots-rag/index.md). The lesson
pages explain the concepts; this code is what you run.

Everything here works offline with the Python standard library plus NumPy. No
account, no API key, no model download, no GPU.

## Quick start

```bash
# from the repository root
python scripts/make_chatbot_data.py                 # synthetic corpus + question sets
python -m pip install -r requirements/base.txt       # numpy only for the core path

cd projects/chatbots-rag
python project_a_faq_bot.py --selftest
python project_f_cited_assistant.py --selftest
python project_g_evaluation.py --split test
```

Run every project's built-in checks:

```bash
for p in project_*.py; do echo "== $p"; python "$p" --selftest; done
```

Run the unit tests (from the repository root):

```bash
python -m unittest discover -s tests -v
```

## Which file is which

| Project | File | What it demonstrates |
| --- | --- | --- |
| A | `project_a_faq_bot.py` | Deterministic intents, precedence, explicit fallback |
| B | `project_b_llm_chatbot.py` | Model client, system prompt, bounded history |
| C | `app_streamlit.py` | Chat interface; no logic of its own |
| D | `project_d_local_model.py` | Local inference, resource report, safe fallback |
| E | `project_e_course_docs_bot.py` | The same pipeline over real course documents |
| F | `project_f_cited_assistant.py` | Citations, conflicts, withheld evidence |
| G | `project_g_evaluation.py` | Fixed question set, four configurations, JSON report |
| H | `project_h_domain_assistant.py` | Final assembly, logging, deployment checklist |

Shared modules live in `chatbot_core/`:

| Module | Responsibility |
| --- | --- |
| `documents.py` | Load, split, and chunk text with citation metadata |
| `embeddings.py` | Offline hashing embedder; optional sentence-transformers |
| `retrieval.py` | Dense index, BM25 baseline, hybrid fusion |
| `model_client.py` | Fake, local, and hosted clients behind one interface |
| `generation.py` | Prompt assembly, structured output, abstention, conflicts |
| `citations.py` | Numbering, validation, fabricated-citation detection |
| `guardrails.py` | Injection screening and redaction |
| `history.py` | Conversation state and explicit trimming |
| `logging_safe.py` | Minimal, redacted, hashed-identifier logging |
| `evaluation.py` | Metrics, per-question rows, comparison report |
| `chatbot.py` | Orchestrator used by every project |

## Backends

| Backend | Requires | Use it for |
| --- | --- | --- |
| `fake` (default) | nothing | Every lab, test, and evaluation in this section |
| `local` | a cached transformers model, ~1 GB+ | Module 7, Project D |
| `api` | a key in `.env` and explicit consent | Module 8, optional comparison |

```bash
python project_b_llm_chatbot.py --backend local --model HuggingFaceTB/SmolLM2-360M-Instruct
python project_b_llm_chatbot.py --backend api --consent "your question"
```

The `api` backend refuses to start without `--consent`, because sending document
text to a third party is a decision, not a default.

## Data

`scripts/make_chatbot_data.py` writes `data/chatbots-rag/`:

* `corpus/` - 13 synthetic documents about a fictional Study Hub;
* `adversarial/` - an injection document, a document with personal data, and two
  documents that disagree;
* `dev_questions.json` / `test_questions.json` - questions with gold documents.

The adversarial files are never loaded by default. Tests index them explicitly.

## Known limitations

* `FakeModelClient` is extractive and cannot paraphrase, so its measured accuracy
  on the test set is modest. That is deliberate: it is a test double, and the
  evaluation numbers in the lessons are its honest numbers, not a claim about LLMs.
* `HashingEmbedder` captures surface overlap, not meaning. The section teaches the
  difference by measuring it.
* `app_streamlit.py` requires `requirements/llm.txt` and is not covered by the
  offline test suite.
