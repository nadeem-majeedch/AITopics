# Project D - A local-model chatbot

**Section path:** [Overview](../index.md) · Modules [CA07](../ca07-local-models.md), [CA08](../ca08-hosted-api.md) · **Project D** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 10% of the section assessment |
| **Time** | 4 hours (plus download time if you use a real model) |
| **Hardware** | CPU or optional GPU; the offline path needs neither |
| **Code** | `projects/chatbots-rag/project_d_local_model.py` |
| **Prerequisite** | CA07 |

## The task

Run a compatible instruct model locally behind the existing client interface, measure what
it costs on your machine, and document a fallback that never downloads anything by
accident.

If you cannot run a real model, that is a valid outcome: produce the resource report and a
written analysis instead.

## Run the reference implementation

```bash
cd projects/chatbots-rag
python project_d_local_model.py --budget-check
python project_d_local_model.py --selftest
```

Verified on the authoring machine (Windows 11, Python 3.12.10, CPU only):

```text
python: 3.12.10
platform: Windows-11
disk_free_gb: 81.1
transformers_installed: True
torch_installed: True
cuda_available: False
torch_version: 2.14.1+cpu

client: fake-extractive-v1
note:   no local model requested; using the offline client (no download)
```

The `note:` line is a design requirement, not an accident: a selftest must never start a
gigabyte download.

## What to submit

```text
ca-project-d/
  README.md            # hardware, model id, commands, measured results
  local_chat.py        # your implementation
  budget_report.json   # output of --budget-check
  latency.md           # table: model, prompt, tokens, latency, hardware
  reflection.md        # 200-300 words
```

## Steps

1. **Report the environment** before touching a model: Python, OS, RAM, disk, CUDA.
2. **Estimate** whether your chosen model fits, using the arithmetic in CA07.
3. **Load once, reuse**, and bound `max_new_tokens`.
4. **Measure** end-to-end latency for three prompts of different lengths, at least five
   runs each; report the median, not the best.
5. **Exercise the fallback**: unset the model variable and confirm the offline client is
   used and reported.
6. **Record the licence** of the model you used, and where the weights are cached.

## Expected behaviour

| Scenario | Expected |
| --- | --- |
| No model configured | Offline client, note says no download |
| Model configured and cached | Local client, latency reported |
| Model configured but load fails | Fallback, with the exception type and message |
| Disk nearly full | A warning before any download attempt |
| Repeated prompts | Load cost paid once, not per prompt |

## Test cases to include

| # | Case | Pass condition |
| --- | --- | --- |
| 1 | `--budget-check` | Reports platform, disk, torch, CUDA |
| 2 | No model set | Offline client, no network access attempted |
| 3 | Bad model id | Fallback with a readable note |
| 4 | Latency run | Median reported with hardware and model id |
| 5 | Long prompt | Either answers with truncation noted, or fails clearly |

## Constraints

- Never commit weights, caches, or `*.safetensors`.
- Never let a test trigger a download implicitly.
- Report latency with hardware; a number without a machine is not evidence.
- Respect the model licence, including acceptable-use terms.

## Rubric

| Dimension | Weight | Excellent | Developing |
| --- | --- | --- | --- |
| Resource analysis | 25 | Estimates match measured behaviour, with reasoning | No numbers, or numbers without hardware |
| Integration | 25 | Same interface; no pipeline changes needed | Model calls wired directly into the app |
| Fallback design | 20 | Fallback is explicit, reported, and download-safe | Crashes, or silently substitutes |
| Measurement | 15 | Median over repeats, prompts described | A single timing, rounded |
| Documentation | 15 | Another student reproduces the setup | Missing model id or version |

## Optional API comparison

If and only if you have a key and permission:

```bash
python project_b_llm_chatbot.py --backend api --consent "your question"
```

Record the provider, model id, date, and cost estimate. Do not include the key, and do not
send documents you do not own. Skipping this section is a complete answer; say so.

## Extension tasks

1. **Quantise** and re-measure both quality and latency on the same prompts. Report whether
   the quality change is inside the noise of your measurement.
2. **Batch** five prompts and compare total time with five sequential calls.
3. Add a **warm-up** call and show how much of the first-request latency it removes.

Next: [Project E](e-course-docs-bot.md).
