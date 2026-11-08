"""Project D - Running a compatible language model locally.

This project is about the *deployment* question rather than the modelling one:
what changes when the model runs on the student's own machine, and what do you do
when it does not fit?

The script never assumes a model is available. It reports what it found, measures
latency, and falls back to the offline client with an actionable message.

Run:
    python project_d_local_model.py --selftest
    python project_d_local_model.py --model HuggingFaceTB/SmolLM2-360M-Instruct --prompt "What is RAG?"
    python project_d_local_model.py --budget-check

Resource guidance (measured on this course's authoring machine, CPU-only):

* a 0.3B-0.5B instruct model needs roughly 1-2 GB of RAM in float32 and answers a
  short prompt in seconds, not milliseconds;
* a 3B model is uncomfortable on 8 GB RAM without quantization;
* the download is the first failure, not the inference. Check disk before you
  start, and keep the cache outside the repository (it is gitignored).
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import time

from chatbot_core import FakeModelClient, LocalTransformersClient, SYSTEM_PROMPT


def disk_free_gb(path: str = ".") -> float:
    return round(shutil.disk_usage(path).free / (1024**3), 1)


def environment_report() -> dict:
    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "disk_free_gb": disk_free_gb(),
        "transformers_installed": False,
        "torch_installed": False,
        "cuda_available": False,
        "model_env": os.environ.get("CHATBOT_LOCAL_MODEL", ""),
    }
    try:
        import transformers  # noqa: F401

        report["transformers_installed"] = True
    except ImportError:
        pass
    try:
        import torch

        report["torch_installed"] = True
        report["cuda_available"] = bool(torch.cuda.is_available())
        report["torch_version"] = torch.__version__
    except ImportError:
        pass
    return report


def load_local(model_id: str | None):
    """Return ``(client, note)``. Falls back instead of raising, by design.

    Nothing is downloaded unless a model was requested explicitly. An accidental
    multi-hundred-megabyte download is the most common way a lab dies, so the
    default path never touches the network.
    """
    if not model_id:
        return FakeModelClient(), "no local model requested; using the offline client (no download)"
    try:
        return LocalTransformersClient(model_id), "local model loaded"
    except Exception as exc:  # noqa: BLE001 - the fallback is the point of this function
        return FakeModelClient(), f"local model unavailable ({type(exc).__name__}: {exc}); using offline client"


def timed_turn(client, prompt: str) -> tuple[str, float]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    started = time.perf_counter()
    text = client.complete(messages)
    return text, (time.perf_counter() - started) * 1000.0


def selftest() -> int:
    report = environment_report()
    print("environment:")
    for key, value in report.items():
        print(f"  {key}: {value}")

    client, note = load_local(os.environ.get("CHATBOT_LOCAL_MODEL") or None)
    print(f"\nclient: {client.name}\nnote:   {note}")

    text, latency = timed_turn(client, "Explain retrieval-augmented generation in one sentence.")
    print(f"\nlatency: {latency:.1f} ms\nreply:   {text[:200]}")

    failures = 0
    if report["disk_free_gb"] < 2:
        print("WARN  less than 2 GB free disk; a model download will fail")
    if latency <= 0:
        print("FAIL  latency was not measured")
        failures += 1
    if not isinstance(text, str) or not text.strip():
        print("FAIL  client returned no text")
        failures += 1
    print(f"\n{failures} failure(s)")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Project D: local model chatbot")
    parser.add_argument("--model", default=None)
    parser.add_argument("--prompt", default="Explain retrieval-augmented generation in one sentence.")
    parser.add_argument("--budget-check", action="store_true", help="print environment and exit")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.budget_check:
        for key, value in environment_report().items():
            print(f"{key}: {value}")
        return 0
    if args.selftest:
        return selftest()

    model_id = args.model or os.environ.get("CHATBOT_LOCAL_MODEL") or None
    client, note = load_local(model_id)
    print(f"client: {client.name}\nnote:   {note}\n")
    text, latency = timed_turn(client, args.prompt)
    print(text)
    print(f"\n[{latency:.1f} ms]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
