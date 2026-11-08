# P05 - Local AI assistant with a graphical interface

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Intermediate |
| **Effort** | 40-50 hours |
| **Hardware** | CPU-only; 8 GB RAM comfortable. A local model needs 2-6 GB of disk |
| **Prerequisites** | [CA03 calling a model](../../lessons/chatbots-rag/ca03-calling-a-model.md), [CA04 history and context](../../lessons/chatbots-rag/ca04-history-and-context.md), [CA06 Streamlit interface](../../lessons/chatbots-rag/ca06-streamlit-interface.md), [CA07 local models](../../lessons/chatbots-rag/ca07-local-models.md), [CA16 privacy](../../lessons/chatbots-rag/ca16-privacy-and-deployment.md) |
| **Builds on** | Conversational AI projects C and D |

## 1. Problem statement and motivation

Most "AI assistant" tutorials assume a hosted API, a stable network, and a user who
is comfortable with a terminal. This project builds the opposite: an assistant that
runs on one machine, keeps conversation data local, degrades gracefully when no
model is available, and can be operated by someone who has never used a command
line.

The interface is the engineering problem, not decoration. A desktop application
must handle a model that is still loading, a prompt that is too long, a crash
mid-generation, and a user who closes the window during work.

**Decision supported:** whether a non-technical user can complete a bounded task
(draft, summarise, search their own notes) without the network.

## 2. Intended learning outcomes

1. Separate the assistant core from the interface so both can be tested.
2. Implement a streaming generation loop with cancellation and error states.
3. Manage conversation history under a token budget with an explicit truncation
   policy.
4. Package a local model or a deterministic fallback so the app runs with no
   network.
5. Handle failure states visibly: model missing, out of memory, timeout, invalid input.
6. Keep data local and prove it: no telemetry, no network calls in the default mode.
7. Run a small usability test and report what users actually did.

## 3. Difficulty and prerequisites

**Level:** Intermediate. 40-50 hours: 10 core, 12 interface, 8 packaging, 8
testing, 6 usability, 6 writing.

Requires CA03-CA07. You should have called a model from Python and handled a
timeout. No prior GUI experience is assumed; Tkinter ships with Python.

## 4. Scope and out-of-scope features

**In scope**

- A desktop GUI (Tkinter recommended because it is in the standard library;
  Streamlit is acceptable if you document how to launch it).
- One assistant core with two backends: a local model and a deterministic
  rule-based fallback used when no model is installed.
- Streaming output with a stop button.
- History with a token budget and a documented summarise-or-drop policy.
- Local-only storage of history, with a delete button that actually deletes.
- A packaging story: one command to launch, dependencies pinned, model path
  configurable.

**Out of scope**

- Multi-user accounts, cloud sync, or remote access.
- Mobile apps and browser extensions.
- Voice input (that is P08) and document retrieval (that is P04), unless you add
  them as an extension with their own evaluation.
- Fine-tuning (P03).
- Distribution to an app store, code signing, or auto-update infrastructure.

## 5. Dataset options, licences, and preparation

There is no training dataset. The "data" is the model and the user's own inputs.

| Component | Option | Licence | Notes |
| --- | --- | --- | --- |
| Local model | A GGUF build of a small instruct model run through `llama.cpp` or Ollama | Check the model card; Apache-2.0 and MIT models exist | Record the exact model file, quantisation, and hash |
| No model available | Deterministic fallback rules you write | Yours | Must be honest: it answers a small set of intents and says so |
| Test prompts | 30 prompts you write, covering short, long, ambiguous, unsafe | Yours | Commit the prompts, not the personal data |
| Optional notes corpus | Your own text files | Yours | Use only non-personal notes; document deletion |

**Preparation**

1. Decide the backend. If you cannot download a model, build the fallback first
   and treat the model as an optional upgrade; the project is still completable.
2. Record the model file's SHA-256 and size in `models/manifest.json`.
3. Write 30 test prompts before building the UI, so the core can be tested without
   a screen.
4. Decide where history is stored (a JSON file under the user's home directory is
   fine) and what "delete" means: remove the file, or remove the rows.

## 6. Recommended baseline

**Terminal chat loop with the fallback backend.** Ten lines: read a line, call the
core, print the reply. This proves the core works before any widget exists, and it
is the reference behaviour the GUI must match.

Second baseline: the same loop with the local model, no streaming. Streaming is an
improvement you must justify with a measured time-to-first-token.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Core and fallback | Terminal loop, 30 prompts answered, unit tests | 10 |
| 2 | Local model backend | Same prompts, model manifest, latency table | 8 |
| 3 | GUI | Send, stream, stop, clear, delete history | 12 |
| 4 | Failure states | Screenshots or transcripts for five failure modes | 6 |
| 5 | Packaging and privacy | Clean install on a fresh environment, network check | 8 |
| 6 | Usability and report | Three testers, task list, observations, report | 8 |

## 8. Repository or folder structure

```text
capstone-p05/
  README.md
  requirements.txt
  run.py                  # launcher: python run.py
  config.example.json     # model path, max tokens, history path
  src/
    assistant/
      core.py             # generate(prompt, history) -> tokens
      backends/
        local_model.py
        fallback.py
      history.py          # token budget, truncation, persistence
      errors.py           # typed errors the UI can render
    ui/
      app.py              # Tkinter application
      widgets.py
  models/
    manifest.json         # filename, sha256, size, licence, source
  tests/
    test_core.py
    test_history.py
    test_backends.py
  docs/
    privacy.md
    usability-notes.md
  reports/
    report.md
```

## 9. Detailed development tasks

1. `core.py`: a `generate(prompt, history, cancel_event)` generator yielding text
   chunks. No UI imports. Type the errors: `ModelMissing`, `ContextTooLong`,
   `BackendCrash`, `Cancelled`.
2. `fallback.py`: rules for at least six intents (greeting, summarise-this-text,
   rewrite-formally, explain-word, draft-email, unknown). Unknown must say it does
   not know, not improvise.
3. `local_model.py`: load the model once, keep it warm, stream tokens, respect a
   stop flag. Measure time to first token and tokens per second.
4. `history.py`: keep the last N tokens using the model's tokeniser when available
   and a documented approximation otherwise. Test the boundary: a message that
   alone exceeds the budget must be truncated with a visible notice, not silently.
5. `ui/app.py`: message list, input box, send, stop, clear, delete-history, model
   status indicator, and an error banner. Keyboard-only operation must work: Tab
   order, Enter to send, Escape to stop.
6. Streaming in the UI: append to the last message on a timer or queue; never block
   the event loop. A frozen window during generation is a failure.
7. Cancellation: the stop button sets the event, the backend stops within one
   chunk, and the partial reply is kept with a "(stopped)" marker.
8. Failure states, each with a distinct message and a recovery action: model file
   missing, model too large for memory, generation timeout, empty input, history
   file corrupt.
9. Privacy: the default mode makes no network calls. Prove it by running with the
   network disabled, and by asserting in a test that the local backend does not
   import an HTTP client.
10. Delete: remove the history file, confirm with a dialog, and verify the file is
    gone. If the OS keeps backups, say so.
11. Packaging: `python run.py` from a fresh virtual environment, with
    `config.example.json` copied to `config.json`. The README lists the exact
    commands for Windows and Linux.
12. Usability: three people who are not you attempt four tasks (send a message,
    stop a long reply, clear history, find out why the model is unavailable). Record
    completion, time, and one quote each. Do not coach them.

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| Core unit tests | Logic is independent of the UI | 10 prompts produce typed results with no display |
| History budget test | Truncation is bounded | Rendered prompt never exceeds the configured budget |
| Backend parity | Both backends satisfy the interface | Same call signature, same error types |
| Cancellation test | Stop works | Generation ends within 200 ms of the event |
| Offline test | No hidden network use | App runs with networking disabled |
| Delete test | Data is actually removed | History file absent after delete |
| GUI smoke test | Window constructs | App builds and closes cleanly where a display exists |

Protocol: functional checks automated where possible; GUI behaviour recorded as a
scripted manual transcript because automated GUI testing is out of scope for this
course. Say that explicitly instead of implying full automation.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| Time to first token (median, p95) | Perceived responsiveness |
| Tokens per second | Whether streaming is usable |
| Memory peak while loaded | The real hardware constraint |
| Task completion rate in usability test (n=3) | Whether the interface works |
| Time on task per usability task | Where users struggle |
| Failure-state coverage | Five states, five messages, five recoveries |

**Qualitative**

- Quotes from the three testers, including confusion.
- Whether the fallback is honest: does it ever pretend to know?
- Accessibility observations: keyboard-only run, font scaling, contrast.

## 12. Expected deliverables

- [ ] `python run.py` launches the app on a clean environment.
- [ ] Model manifest with hash, size, licence, and source.
- [ ] Fallback backend with six documented intents and an honest unknown.
- [ ] Five failure states implemented and transcribed.
- [ ] Privacy note: what is stored, where, for how long, how to delete.
- [ ] Usability notes with three testers and four tasks.
- [ ] Latency and memory table.
- [ ] Report and reflection.

## 13. Suggested extensions

- Add a document sidebar that lets the user chat with one local text file, with
  citations (links to P04).
- Add a "copy reply" and "export conversation" action, and test what export
  includes.
- Add a model picker that lists installed GGUF files with sizes, and refuses to
  load one that will not fit in available memory.
- Add a screen-reader pass and report what changed.

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Window freezes during generation | Generation on the UI thread | Run the backend in a worker thread and feed a queue |
| Text appears all at once | No streaming, or buffering the whole reply | Yield chunks and render incrementally |
| Stop button does nothing | Event not checked inside the loop | Check the cancel event every chunk |
| App crashes on missing model | Unhandled exception at load | Catch, show `ModelMissing`, offer fallback |
| History grows until the model errors | No token budget | Truncate with a visible notice; test the boundary |
| "Offline" app still calls the network | Telemetry, update check, or a hosted default | Remove it, then test with networking disabled |
| Delete leaves data behind | Deleting rows but not the file, or a second copy | Delete the file and any temp copy; verify |
| Tkinter missing on Linux | Minimal Python install without Tk | Document the package name; fail with a clear message |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Architecture and code quality | 20% | Core/UI separation, typed errors, tests, no UI imports in core | Clear separation with tests | Monolithic but working | Untestable code |
| Interface and interaction | 25% | Streaming, cancellation, keyboard operation, clear states | Usable interface with the main controls | Works but confusing or blocking | Unusable |
| Failure handling | 15% | Five states with recovery, transcribed | Main failures handled | Some crashes | Crashes on common errors |
| Local-first and privacy | 15% | Verified offline, deletion proven, storage documented | Data kept local, documented | Unclear data handling | Silent network or data leaks |
| Packaging and reproducibility | 15% | Fresh-environment run, pinned deps, model manifest | Documented setup | Manual steps assumed | Does not run elsewhere |
| Evaluation and communication | 10% | Usability test with real observations, honest limits | Basic user testing | No user testing | Claims without evidence |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 works, evidence thin; below
70 the app is not operable by someone else.

## 16. Self-review checklist

- [ ] `python run.py` works from a fresh virtual environment.
- [ ] The app runs with networking disabled.
- [ ] Model file, quantisation, licence, and hash are recorded.
- [ ] Stop works within 200 ms and keeps the partial reply.
- [ ] History is bounded by tokens and truncation is visible.
- [ ] Delete removes the stored conversation and I verified it.
- [ ] Five failure states show distinct messages.
- [ ] Keyboard-only operation works.
- [ ] Three testers completed four tasks without coaching.
- [ ] No secrets or personal data are in the repository.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Architecture** - a small diagram of UI, core, backends, history, storage.
2. **Backend comparison** - fallback versus local model, with latency and quality
   observations from the same 30 prompts.
3. **Failure-state table** - state, message shown, recovery action, test evidence.
4. **Usability** - task, completion, time, quote, change made as a result.

## 18. Demonstration and presentation checklist

- [ ] Launch from a terminal, send a prompt, stop mid-reply.
- [ ] Remove the model file and show the missing-model state and fallback.
- [ ] Send a message that exceeds the budget and show the truncation notice.
- [ ] Delete history and show the file is gone.
- [ ] Show the offline proof (network disabled).
- [ ] Quote one usability failure and the change you made.
- [ ] Answer: "What stops this from being a product?" with a specific list.

**Demo trap:** demoing only the happy path with a model already loaded. The failure
states are the project.

---

**Previous:** [P04 grounded chatbot](p04-grounded-chatbot.md) · **Next:** [P06 image classifier](p06-image-classifier.md) · [Index](index.md)
