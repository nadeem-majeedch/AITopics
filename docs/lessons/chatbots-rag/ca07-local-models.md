# CA07 - Running a compatible language model locally {#ca07}

**Section path:** [Overview](index.md) · **Module 7** · [Projects](index.md#the-projects) · [Assessment](assessment.md)

| | |
| --- | --- |
| **Study time** | 4 hours: 2 h reading, 2 h Project D |
| **Hardware** | CPU or optional GPU; a model download is required for the real path |
| **Prerequisites** | CA03, CA06 |
| **You will produce** | A local-model chatbot, a resource report, and a measured latency figure |

## Why this module exists

Local inference is the reason this course can promise that your documents never leave
your machine. It is also where students hit the wall that tutorials hide: the model
does not fit, the download is slow, the first token takes eight seconds, and nobody
told them what "fits" means.

This module is about the deployment arithmetic, not the modelling. You will measure
what you have and choose accordingly.

## The resource arithmetic

Three quantities decide whether a model runs on your machine:

| Quantity | Rough rule | What it controls |
| --- | --- | --- |
| Disk | Model size, roughly 2 bytes per parameter in fp16 | Whether you can download it |
| RAM / VRAM | Model size plus 20-40% for activations and context | Whether it loads at all |
| Compute | Tokens per second, CPU is 10-100x slower than a GPU | Whether it is usable interactively |

Concrete expectations for an instruct model in fp16:

| Parameters | Weights (approx.) | Laptop CPU | 8 GB GPU |
| --- | --- | --- | --- |
| 0.36B | 0.7 GB | Works; a few seconds per short answer | Comfortable |
| 0.5B | 1.0 GB | Works; noticeable latency | Comfortable |
| 1.5B | 3 GB | Slow but usable for batch work | Fits with a small context |
| 3B | 6 GB | Painful interactively | Tight; quantise |
| 7B | 14 GB | Not practical | Needs 4-bit quantization |

These are planning numbers, not promises. Measure on your own machine and record the
result; a latency claim without hardware is not reproducible.

## The installation path

```bash
python -m pip install -r requirements/cpu.txt     # CPU-only PyTorch wheel
python -m pip install -r requirements/llm.txt     # transformers extras if needed
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

The CPU index URL in `requirements/cpu.txt` matters: without it, pip may pull CUDA
libraries that are hundreds of megabytes and useless on a machine without an NVIDIA
card.

## Loading a model

```python
from transformers import pipeline

pipe = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-360M-Instruct")
output = pipe(messages, max_new_tokens=256, do_sample=False)
```

Two habits that prevent most local-model pain:

1. **Load once, reuse.** Constructing the pipeline per request reloads gigabytes.
2. **Bound the output.** `max_new_tokens=256` is a policy, not a suggestion; an
   unbounded generation can run for minutes on CPU.

## Falling back instead of crashing

`project_d_local_model.py` never assumes a model is present:

```python
def load_local(model_id: str | None):
    if not model_id:
        return FakeModelClient(), "no local model requested; using the offline client (no download)"
    try:
        return LocalTransformersClient(model_id), "local model loaded"
    except Exception as exc:
        return FakeModelClient(), f"local model unavailable ({type(exc).__name__}: {exc}); using offline client"
```

The `if not model_id` guard is not politeness. Without it, a routine `--selftest` can
start a multi-hundred-megabyte download on a metered connection. A lab must never do
that implicitly.

The fallback is *reported*, not hidden: the script prints which client answered. A
silent fallback is worse than a crash, because the student concludes the model works
when it never ran.

## Measuring what you have

```bash
python project_d_local_model.py --budget-check
```

Reports Python, platform, free disk, whether torch and transformers are installed, and
CUDA availability. On the authoring machine (CPU-only):

```text
python: 3.12.10
platform: Windows-11
disk_free_gb: 81.1
transformers_installed: True
torch_installed: True
cuda_available: False
```

Latency measurement is deliberately naive — `time.perf_counter()` around one call —
because the interesting number is the order of magnitude, and a rigorous benchmark is
Module 8's comparison work.

## Quantization, briefly

4-bit quantization reduces weight memory roughly fourfold at some quality cost. It is
the difference between "7B will not run" and "7B runs slowly" on a laptop. Two rules:

- **Evaluate after quantizing.** Do not assume parity; run your question set.
- **Prefer a documented format** (GGUF via llama.cpp, or bitsandbytes for transformers)
  and record exactly what you used.

This section does not require quantization. It requires you to know it exists and to
state which configuration your numbers came from.

## Licensing and provenance

A model is licensed software. Before you ship:

- read the model card's licence and acceptable-use terms;
- record the exact model id and revision;
- keep the cache outside the repository (`.gitignore` already excludes `models/` and
  `*.safetensors`);
- never commit weights.

Some small instruct models are permissively licensed; others carry use restrictions.
"The weights downloaded automatically" is not a licence.

## The local-versus-hosted decision

| Factor | Favours local | Favours hosted |
| --- | --- | --- |
| Private documents | Yes, by default | Only with explicit consent |
| Quality on hard questions | Weaker at small sizes | Stronger |
| Latency | Depends on hardware | Usually lower, network permitting |
| Cost | Electricity and time | Per token |
| Reproducibility | You pin the weights | Provider updates silently |
| Availability | Works offline | Needs network and a key |

For this course the answer is local, because the learning objective is the pipeline and
because no student should need a paid account to finish.

## Common failures and how to diagnose them

| Symptom | Likely cause | First check |
| --- | --- | --- |
| `ImportError: transformers` | Optional stack not installed | `pip install -r requirements/llm.txt` |
| Download stalls or fails | Network, disk, or cache permissions | `--budget-check`; check free space |
| Killed during load (OOM) | Model plus context exceeds RAM | Smaller model, smaller context, or quantize |
| First token takes 10+ seconds | CPU inference on a larger model | Expected; reduce model or use batch mode |
| Answers are repetitive | Small model, greedy decoding, weak prompt | Lower `max_new_tokens`, adjust prompt, try sampling |
| Model ignores the evidence | Model too small for instruction following | Record it: this is a finding, not a bug to hide |
| CUDA out of memory | Context or batch too large | Reduce context, batch size, or precision |

## Checkpoint

- [ ] You can estimate disk and memory for a model from its parameter count.
- [ ] You can explain why `load_local(None)` must not download anything.
- [ ] You can state the hardware your latency number came from.
- [ ] You can name one licensing obligation of shipping a local model.

## Next step

Read [CA08 - A hosted model API as an optional alternative](ca08-hosted-api.md), then
complete [Project D](projects/d-local-model.md).
