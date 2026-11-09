"""Verify that every advertised module has its real lesson, notebook, lab, and assessment.

Run from the repository root:

    python scripts/check_course_inventory.py

The course makes claims in several indexes. This script checks those claims against
the filesystem instead of trusting a table:

* every module M00-M17 has the lesson pages it advertises;
* every module that promises a guided notebook has one, and every notebook is
  listed in ``mkdocs.yml`` navigation;
* every foundation and applied module has a lab or project brief and an assessment,
  except the orientation module and the capstone notebook (both documented as
  not applicable);
* every notebook is valid JSON, executed, free of stored error outputs, and long
  enough to be a tutorial rather than a title or an outline;
* no directory under ``notebooks/`` is an empty placeholder;
* the six notebooks written to the 14-section standard contain all fourteen
  sections.

Exit status is 0 when clean and 1 when a content claim is not backed by a file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import nbformat
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
NOTEBOOKS = ROOT / "notebooks"

# Lessons are grouped exactly as the course teaches them. CV08-CV10 are shared by
# M11 and M12, so the assignment count is larger than the unique file count.
FOUNDATION = [
    ("F01", "f01-python-ai", "f01_python_ai"),
    ("F02", "m01-environment", "m01_environment_check"),
    ("F03", "f03-numpy-pandas", "f03_numpy_pandas"),
    ("F04", "f04-data-cleaning", "f04_data_cleaning"),
    ("F05", "f05-splits", "f05_splits"),
    ("F06", "f06-eda", "f06_eda"),
    ("F07", "f07-supervised-unsupervised", "f07_supervised_unsupervised"),
    ("F08", "f08-regression-classification", "f08_regression_classification"),
    ("F09", "f09-tree-ensembles", "f09_tree_ensembles"),
    ("F10", "f10-metrics-validation", "f10_metrics_validation"),
    ("F11", "f11-neural-networks", "f11_neural_networks"),
    ("F12", "f12-backpropagation", "f12_backpropagation"),
    ("F13", "f13-reproducibility", "f13_reproducibility"),
]

MODULES = [
    {
        "code": "M00",
        "title": "Course orientation and study plan",
        "lessons": ["docs/syllabus/level-0-start.md"],
        "notebooks": [],
        "labs": [],
        "assessments": [],
        "not_applicable": {"notebook": "orientation is a study plan, not a guided notebook"},
    },
    {
        "code": "M01",
        "title": "Python and AI development environment",
        "lessons": ["docs/lessons/m01-environment/index.md"],
        "notebooks": ["notebooks/foundations/m01_environment_check.ipynb"],
        "labs": ["docs/lessons/m01-environment/lab.md"],
        "assessments": ["docs/lessons/m01-environment/assessment.md"],
    },
    {
        "code": "M02",
        "title": "Machine learning foundations",
        "lessons": [f"docs/lessons/{slug}/index.md" for unit, slug, _ in FOUNDATION[2:10]],
        "notebooks": [f"notebooks/foundations/{stem}.ipynb" for unit, slug, stem in FOUNDATION[2:10]],
        "labs": [f"docs/lessons/{slug}/lab.md" for unit, slug, _ in FOUNDATION[2:10]],
        "assessments": [f"docs/lessons/{slug}/assessment.md" for unit, slug, _ in FOUNDATION[2:10]],
    },
    {
        "code": "M03",
        "title": "Deep learning foundations",
        "lessons": [f"docs/lessons/{slug}/index.md" for unit, slug, _ in FOUNDATION[10:]],
        "notebooks": [f"notebooks/foundations/{stem}.ipynb" for unit, slug, stem in FOUNDATION[10:]],
        "labs": [f"docs/lessons/{slug}/lab.md" for unit, slug, _ in FOUNDATION[10:]],
        "assessments": [f"docs/lessons/{slug}/assessment.md" for unit, slug, _ in FOUNDATION[10:]],
    },
    {
        "code": "M04",
        "title": "Training models from scratch",
        "lessons": [f"docs/lessons/model-training/mt{i:02d}-{slug}.md" for i, slug in [
            (1, "training-loop"), (2, "loss-and-optimizer"), (3, "augmentation-and-regularization"),
            (4, "evaluation-and-error-analysis"), (5, "checkpoints-and-compute")]],
        "notebooks": ["notebooks/model-training/m04_training_from_scratch.ipynb"],
        "labs": ["docs/lessons/model-training/labs/lab-1-training-ablation.md",
                 "docs/lessons/model-training/labs/lab-2-dataset-audit.md"],
        "assessments": ["docs/lessons/model-training/assessment.md"],
    },
    {
        "code": "M05",
        "title": "Dataset preparation, labelling, cleaning, augmentation",
        "lessons": [f"docs/lessons/model-training/mt{i:02d}-{slug}.md" for i, slug in [
            (6, "dataset-audit"), (7, "cleaning-and-labels"), (8, "leakage-and-splits"),
            (9, "label-noise"), (10, "dataset-cards")]],
        "notebooks": ["notebooks/model-training/m05_data_engineering.ipynb"],
        "labs": ["docs/lessons/model-training/labs/lab-1-training-ablation.md",
                 "docs/lessons/model-training/labs/lab-2-dataset-audit.md"],
        "assessments": ["docs/lessons/model-training/assessment.md"],
    },
    {
        "code": "M06",
        "title": "Transformers and language models",
        "lessons": [f"docs/lessons/llm-fine-tuning/lf0{i}-{slug}.md" for i, slug in [
            (1, "tokens-and-embeddings"), (2, "attention"), (3, "transformer-block"), (4, "tiny-lm-training")]],
        "notebooks": ["notebooks/llm-fine-tuning/m06_transformers.ipynb"],
        "labs": ["docs/lessons/llm-fine-tuning/labs/lab-1-tiny-lm.md",
                 "docs/lessons/llm-fine-tuning/labs/lab-2-sft-and-lora.md",
                 "docs/lessons/llm-fine-tuning/labs/lab-3-efficiency-report.md"],
        "assessments": ["docs/lessons/llm-fine-tuning/assessment.md"],
    },
    {
        "code": "M07",
        "title": "Small language models and supervised fine-tuning",
        "lessons": [f"docs/lessons/llm-fine-tuning/lf0{i}-{slug}.md" for i, slug in [
            (5, "sft-data-and-templates"), (6, "sft-loss-and-masking"), (7, "evaluating-assistants")]],
        "notebooks": ["notebooks/llm-fine-tuning/m07_sft_small_lm.ipynb"],
        "labs": ["docs/lessons/llm-fine-tuning/labs/lab-1-tiny-lm.md",
                 "docs/lessons/llm-fine-tuning/labs/lab-2-sft-and-lora.md",
                 "docs/lessons/llm-fine-tuning/labs/lab-3-efficiency-report.md"],
        "assessments": ["docs/lessons/llm-fine-tuning/assessment.md"],
    },
    {
        "code": "M08",
        "title": "LoRA, QLoRA, quantization, efficient training",
        "lessons": [f"docs/lessons/llm-fine-tuning/lf{i:02d}-{slug}.md" for i, slug in [
            (8, "lora"), (9, "quantization-and-qlora"), (10, "merging-and-serving")]],
        "notebooks": ["notebooks/llm-fine-tuning/m08_lora_qlora.ipynb"],
        "labs": ["docs/lessons/llm-fine-tuning/labs/lab-1-tiny-lm.md",
                 "docs/lessons/llm-fine-tuning/labs/lab-2-sft-and-lora.md",
                 "docs/lessons/llm-fine-tuning/labs/lab-3-efficiency-report.md"],
        "assessments": ["docs/lessons/llm-fine-tuning/assessment.md"],
    },
    {
        "code": "M09",
        "title": "Chatbots and conversational applications",
        "lessons": [f"docs/lessons/chatbots-rag/ca{i:02d}-{slug}.md" for i, slug in [
            (1, "what-is-a-chatbot"), (2, "chatbot-types"), (3, "calling-a-model"),
            (4, "history-and-context"), (5, "prompts-and-structured-output"),
            (6, "streamlit-interface"), (7, "local-models"), (8, "hosted-api")]],
        "notebooks": ["notebooks/chatbots-rag/m09_chatbots.ipynb"],
        "labs": [f"docs/lessons/chatbots-rag/projects/{name}.md" for name in [
            "a-faq-bot", "b-llm-chatbot", "c-streamlit-app", "d-local-model",
            "e-course-docs-bot", "f-cited-assistant", "g-evaluation", "h-domain-assistant"]],
        "assessments": ["docs/lessons/chatbots-rag/assessment.md"],
    },
    {
        "code": "M10",
        "title": "Embeddings, vector search, and retrieval-augmented generation",
        "lessons": [f"docs/lessons/chatbots-rag/ca{i:02d}-{slug}.md" for i, slug in [
            (9, "embeddings"), (10, "chunking"), (11, "vector-search"), (12, "rag"),
            (13, "citations-and-abstention"), (14, "evaluation"), (15, "fine-tuned-models"),
            (16, "privacy-and-deployment")]],
        "notebooks": ["notebooks/chatbots-rag/m10_rag.ipynb"],
        "labs": [f"docs/lessons/chatbots-rag/projects/{name}.md" for name in [
            "a-faq-bot", "b-llm-chatbot", "c-streamlit-app", "d-local-model",
            "e-course-docs-bot", "f-cited-assistant", "g-evaluation", "h-domain-assistant"]],
        "assessments": ["docs/lessons/chatbots-rag/assessment.md"],
    },
    {
        "code": "M11",
        "title": "Image classification and computer vision",
        "lessons": [f"docs/lessons/computer-vision/cv{i:02d}-{slug}.md" for i, slug in [
            (1, "digital-images"), (2, "datasets-and-annotation-formats"),
            (3, "preprocessing-and-augmentation"), (4, "convolutional-networks"),
            (5, "classification-from-scratch"), (6, "transfer-learning"), (7, "fine-tuning"),
            (8, "training-detectors"), (9, "boxes-iou-map"), (10, "segmentation")]],
        "notebooks": ["notebooks/computer-vision/m11_image_classification.ipynb"],
        "labs": [f"docs/lessons/computer-vision/labs/{name}.md" for name in [
            "lab1-licensed-dataset-classifier", "lab2-cnn-learning-curves", "lab3-scratch-vs-transfer",
            "lab4-finetune-everyday-objects", "lab5-annotate-and-train-detector",
            "lab6-detector-thresholds", "lab7-similarity-app", "lab8-deployment-comparison"]],
        "assessments": ["docs/lessons/computer-vision/assessment.md"],
    },
    {
        "code": "M12",
        "title": "Object detection, tracking, transfer learning",
        "lessons": [f"docs/lessons/computer-vision/cv{i:02d}-{slug}.md" for i, slug in [
            (8, "training-detectors"), (9, "boxes-iou-map"), (10, "segmentation"),
            (11, "face-detection-vs-recognition"), (12, "embeddings-and-similarity"),
            (13, "optimization-and-inference"), (14, "evaluation-robustness-deployment")]],
        "notebooks": ["notebooks/computer-vision/m12_object_detection.ipynb"],
        "labs": [f"docs/lessons/computer-vision/labs/{name}.md" for name in [
            "lab1-licensed-dataset-classifier", "lab2-cnn-learning-curves", "lab3-scratch-vs-transfer",
            "lab4-finetune-everyday-objects", "lab5-annotate-and-train-detector",
            "lab6-detector-thresholds", "lab7-similarity-app", "lab8-deployment-comparison"]],
        "assessments": ["docs/lessons/computer-vision/assessment.md"],
    },
    {
        "code": "M13",
        "title": "Speech recognition, audio classification, speech generation",
        "lessons": [f"docs/lessons/speech-audio/sa{i:02d}-{slug}.md" for i, slug in [
            (1, "audio-fundamentals"), (2, "loading-and-preprocessing"),
            (3, "waveform-spectrogram-mel"), (4, "segmentation-and-datasets"),
            (5, "classical-classification"), (6, "neural-audio-classifier"),
            (7, "asr-and-stt"), (8, "wer-and-transcription-evaluation"),
            (9, "adapting-pretrained-asr"), (10, "tts-and-speech-generation"),
            (11, "speaker-embeddings-and-diarization"), (12, "audio-event-detection"),
            (13, "voice-chatbot"), (14, "optimization-and-deployment")]],
        "notebooks": ["notebooks/speech-audio/m13_speech_audio.ipynb"],
        "labs": [f"docs/lessons/speech-audio/labs/{name}.md" for name in [
            "lab-a-environmental-sound-classifier", "lab-b-waveform-vs-spectrogram",
            "lab-c-transcribe-clip", "lab-d-wer-evaluation", "lab-e-adaptation",
            "lab-f-stt-interface", "lab-g-voice-chatbot", "lab-h-model-comparison"]],
        "assessments": ["docs/lessons/speech-audio/assessment.md"],
    },
    {
        "code": "M14",
        "title": "Video understanding and video analytics",
        "lessons": [f"docs/lessons/video-ai/vd{i:02d}-{slug}.md" for i, slug in [
            (1, "digital-video"), (2, "reading-and-writing"), (3, "frame-extraction-and-datasets"),
            (4, "labelling-and-annotation-formats"), (5, "image-vs-temporal-models"),
            (6, "detection-on-frames"), (7, "tracking-and-track-ids"),
            (8, "counting-and-traffic-flow"), (9, "vehicle-classification-and-adaptation"),
            (10, "clothing-and-appearance"), (11, "action-recognition"),
            (12, "video-classification-and-events"), (13, "fine-tuning"),
            (14, "evaluation-and-deployment"), (15, "responsible-video-analytics")]],
        "notebooks": ["notebooks/video-ai/m14_video_ai.ipynb"],
        "labs": [f"docs/lessons/video-ai/labs/{name}.md" for name in [
            "lab-1-preprocessing", "lab-2-object-detection", "lab-3-tracking-and-counting",
            "lab-4-domain-adaptation", "lab-5-garment-attributes", "lab-6-action-recognition",
            "lab-7-integrated-analytics", "lab-8-performance"]],
        "assessments": ["docs/lessons/video-ai/assessment.md"],
    },
    {
        "code": "M15",
        "title": "AI agents, tool calling, memory, workflows",
        "lessons": [f"docs/lessons/ai-agents/ag{i:02d}-{slug}.md" for i, slug in [
            (1, "agent-loop"), (2, "tool-schemas"), (3, "memory-and-state"),
            (4, "budgets-and-approvals"), (5, "injection-and-evaluation")]],
        "notebooks": ["notebooks/ai-agents/m15_agents.ipynb"],
        "labs": ["docs/lessons/ai-agents/labs/lab-1-support-agent.md"],
        "assessments": ["docs/lessons/ai-agents/assessment.md"],
    },
    {
        "code": "M16",
        "title": "Evaluation, security, responsible AI, deployment",
        "lessons": [f"docs/lessons/production/pr{i:02d}-{slug}.md" for i, slug in [
            (1, "metrics-and-intervals"), (2, "calibration"), (3, "drift"),
            (4, "guardrails-and-cards"), (5, "artifacts-and-serving")]],
        "notebooks": ["notebooks/production/m16_production.ipynb"],
        "labs": ["docs/lessons/production/labs/lab-1-evaluation-and-serving.md"],
        "assessments": ["docs/lessons/production/assessment.md"],
    },
    {
        "code": "M17",
        "title": "Integrated capstone",
        "lessons": [f"docs/lessons/capstone/cp0{i}-{slug}.md" for i, slug in [
            (1, "scoping-and-data"), (2, "build-and-evidence"), (3, "evaluation-and-packaging")]],
        "notebooks": [],
        "labs": ["docs/lessons/capstone/labs/lab-1-capstone-package.md"],
        "assessments": ["docs/lessons/capstone/assessment.md"],
        "not_applicable": {"notebook": "the capstone reuses M04-M16 notebooks in a project"},
    },
]

STANDARD_SECTIONS = [
    "learning objectives",
    "prerequisites",
    "conceptual explanation",
    "terminology",
    "explanation of the code",
    "expected output",
    "interpretation",
    "practical exercises",
    "challenge",
    "limitations",
    "common mistakes",
    "troubleshooting",
    "summary",
    "further reading",
]

STANDARD_NOTEBOOKS = {
    "notebooks/chatbots-rag/m09_chatbots.ipynb",
    "notebooks/chatbots-rag/m10_rag.ipynb",
    "notebooks/computer-vision/m11_image_classification.ipynb",
    "notebooks/computer-vision/m12_object_detection.ipynb",
    "notebooks/speech-audio/m13_speech_audio.ipynb",
    "notebooks/video-ai/m14_video_ai.ipynb",
}


class _Loader(yaml.SafeLoader):
    """SafeLoader that tolerates the pymdownx python/name tag in mkdocs.yml."""


_Loader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", lambda loader, suffix, node: suffix
)


def nav_entries() -> list[str]:
    config = yaml.load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"), Loader=_Loader)
    entries: list[str] = []

    def walk(node) -> None:
        if isinstance(node, str):
            entries.append(node)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)

    walk(config.get("nav", []))
    return entries


def check_notebook(path: Path) -> list[str]:
    problems: list[str] = []
    rel = path.relative_to(ROOT).as_posix()
    try:
        notebook = nbformat.read(path, as_version=4)
    except Exception as exc:
        return [f"{rel}: cannot parse: {type(exc).__name__}: {exc}"]

    try:
        nbformat.validate(notebook)
    except Exception as exc:
        problems.append(f"{rel}: invalid notebook schema: {exc}")

    markdown = [cell.source for cell in notebook.cells if cell.cell_type == "markdown"]
    code = [cell for cell in notebook.cells if cell.cell_type == "code"]
    text = "\n".join(markdown)
    headings = re.findall(r"^#{1,6}\s+\S+", text, flags=re.MULTILINE)

    if len(markdown) < 5:
        problems.append(f"{rel}: only {len(markdown)} markdown cells; looks like an outline")
    if len(code) < 3:
        problems.append(f"{rel}: only {len(code)} code cells; not a runnable tutorial")
    if len(text) < 1_500:
        problems.append(f"{rel}: only {len(text)} characters of explanation")
    if len(headings) < 4:
        problems.append(f"{rel}: only {len(headings)} headings; no recoverable structure")

    for index, cell in enumerate(notebook.cells, start=1):
        if cell.cell_type != "code":
            continue
        if cell.get("execution_count") is None:
            problems.append(f"{rel}: cell {index} has no execution count")
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                problems.append(f"{rel}: cell {index} stores {output.get('ename', 'Error')} output")

    if any(not cell.source.strip() for cell in code):
        problems.append(f"{rel}: contains an empty code cell")

    if rel in STANDARD_NOTEBOOKS:
        lowered = text.lower()
        for section in STANDARD_SECTIONS:
            if section not in lowered:
                problems.append(f"{rel}: missing required section '{section}'")

    return problems


def text_stats(path: Path) -> dict[str, object]:
    """Return the structural measurements used by the inventory and gates."""
    text = path.read_text(encoding="utf-8")
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "words": len(text.split()),
        "h2_headings": len(re.findall(r"^##\s+\S+", text, flags=re.MULTILINE)),
    }


def check_text_resource(path: Path, words: int, headings: int, kind: str) -> list[str]:
    """Reject an outline or placeholder masquerading as a lesson, lab, or test."""
    stats = text_stats(path)
    problems: list[str] = []
    rel = stats["path"]
    if int(stats["words"]) < words:
        problems.append(
            f"{rel}: only {stats['words']} words for a {kind}; expected at least {words}"
        )
    if int(stats["h2_headings"]) < headings:
        problems.append(
            f"{rel}: only {stats['h2_headings']} level-2 sections for a {kind}; "
            f"expected at least {headings}"
        )
    return problems


def notebook_stats(path: Path) -> dict[str, object]:
    """Return inventory fields for one notebook without trusting its filename."""
    rel = path.relative_to(ROOT).as_posix()
    try:
        notebook = nbformat.read(path, as_version=4)
    except Exception as exc:
        return {
            "path": rel,
            "valid": False,
            "substantive": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    markdown = [cell.source for cell in notebook.cells if cell.cell_type == "markdown"]
    code = [cell for cell in notebook.cells if cell.cell_type == "code"]
    errors = [
        output.get("ename", "Error")
        for cell in code
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    executed = all(cell.get("execution_count") is not None for cell in code)
    text = "\n".join(markdown)
    headings = re.findall(r"^#{1,6}\s+\S+", text, flags=re.MULTILINE)
    substantive = (
        len(markdown) >= 5
        and len(code) >= 3
        and len(text) >= 1_500
        and len(headings) >= 4
        and executed
        and not errors
    )
    return {
        "path": rel,
        "valid": True,
        "substantive": substantive,
        "cells": len(notebook.cells),
        "markdown_cells": len(markdown),
        "code_cells": len(code),
        "markdown_words": len(text.split()),
        "headings": len(headings),
        "execution_counts_complete": executed,
        "stored_errors": errors,
        "full_14_section_standard": rel in STANDARD_NOTEBOOKS,
    }


def build_inventory() -> dict[str, object]:
    """Build the machine-readable content inventory from the files on disk."""
    linked: set[Path] = set()
    link_re = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)>#\s]+)")
    for page in DOCS.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for match in link_re.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            linked.add((page.parent / target).resolve())

    modules: list[dict[str, object]] = []
    for module in MODULES:
        module_row: dict[str, object] = {
            "code": module["code"],
            "title": module["title"],
            "lessons": [],
            "notebooks": [],
            "labs": [],
            "assessments": [],
        }
        missing = False
        partial = False
        for kind in ("lessons", "labs", "assessments"):
            threshold = (500, 3) if kind == "lessons" else (300, 4)
            for entry in module[kind]:
                path = ROOT / entry
                if not path.is_file():
                    missing = True
                    module_row[kind].append({"path": entry, "exists": False})
                    continue
                stats = text_stats(path)
                stats["exists"] = True
                stats["linked"] = path.resolve() in linked
                if not stats["linked"] or check_text_resource(path, *threshold, kind):
                    partial = True
                module_row[kind].append(stats)
        for entry in module["notebooks"]:
            path = ROOT / entry
            if not path.is_file():
                missing = True
                module_row["notebooks"].append({"path": entry, "exists": False})
                continue
            stats = notebook_stats(path)
            stats["exists"] = True
            if not stats.get("substantive"):
                partial = True
            module_row["notebooks"].append(stats)
        module_row["status"] = "missing" if missing else "partial" if partial else "complete"
        modules.append(module_row)

    notebooks = [notebook_stats(path) for path in sorted(NOTEBOOKS.rglob("*.ipynb"))]
    expected_lessons = {entry for module in MODULES for entry in module["lessons"]}
    expected_labs = {entry for module in MODULES for entry in module["labs"]}
    expected_assessments = {entry for module in MODULES for entry in module["assessments"]}
    return {
        "generated_on": dt.date.today().isoformat(),
        "definition": {
            "complete": "all advertised files exist, every text resource passes its structural floor, and every notebook is substantive",
            "partial": "every advertised file exists, but a text resource or notebook fails a structural check",
            "missing": "at least one advertised lesson, notebook, lab, or assessment is absent",
            "lesson_floor": "500 words and 3 level-2 headings",
            "lab_floor": "300 words and 4 level-2 headings",
            "assessment_floor": "300 words and 4 level-2 headings",
        },
        "summary": {
            "modules": len(MODULES),
            "lesson_files": len(expected_lessons),
            "notebooks": len(notebooks),
            "labs_and_project_briefs": len(expected_labs),
            "assessments": len(expected_assessments),
            "complete_modules": sum(row["status"] == "complete" for row in modules),
            "partial_modules": sum(row["status"] == "partial" for row in modules),
            "missing_modules": sum(row["status"] == "missing" for row in modules),
            "substantive_notebooks": sum(bool(row.get("substantive")) for row in notebooks),
            "full_14_section_notebooks": sum(
                bool(row.get("full_14_section_standard")) for row in notebooks
            ),
        },
        "modules": modules,
        "notebooks": notebooks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        type=Path,
        help="also write the machine-readable repository inventory to this path",
    )
    args = parser.parse_args(argv)

    problems: list[str] = []
    expected_lessons: set[str] = set()
    expected_labs: set[str] = set()
    expected_assessments: set[str] = set()
    expected_notebooks: set[str] = set()

    for module in MODULES:
        code = module["code"]
        for kind in ("lessons", "labs", "assessments", "notebooks"):
            for entry in module[kind]:
                path = ROOT / entry
                if not path.is_file():
                    problems.append(f"{code}: missing {kind[:-1]} {entry}")
                if kind == "lessons":
                    expected_lessons.add(entry)
                elif kind == "labs":
                    expected_labs.add(entry)
                elif kind == "assessments":
                    expected_assessments.add(entry)
                else:
                    expected_notebooks.add(entry)
        if not module["notebooks"] and "notebook" not in module.get("not_applicable", {}):
            problems.append(f"{code}: no notebook and no documented not-applicable reason")
        if not module["assessments"] and code != "M00":
            problems.append(f"{code}: no assessment file")

    # F01 is a pre-M01 unit with the full four-page structure.
    f01_slug, f01_stem = FOUNDATION[0][1], FOUNDATION[0][2]
    for entry in (
        f"docs/lessons/{f01_slug}/index.md",
        f"docs/lessons/{f01_slug}/lab.md",
        f"docs/lessons/{f01_slug}/assessment.md",
        f"notebooks/foundations/{f01_stem}.ipynb",
    ):
        if not (ROOT / entry).is_file():
            problems.append(f"F01: missing {entry}")

    discovered = sorted(path.relative_to(ROOT).as_posix() for path in NOTEBOOKS.rglob("*.ipynb"))
    expected_notebooks.add("notebooks/foundations/f01_python_ai.ipynb")
    for entry in discovered:
        if entry not in expected_notebooks:
            problems.append(f"notebook is not assigned to any module: {entry}")
    for entry in sorted(expected_notebooks):
        if entry not in discovered:
            problems.append(f"module promises a notebook that does not exist: {entry}")

    for entry in discovered:
        problems.extend(check_notebook(ROOT / entry))

    # Structural floors catch a lesson, lab, or assessment that exists only as a
    # title or outline. They are deliberately low: the human review is separate.
    for kind, entries, floor in (
        ("lesson", expected_lessons, (500, 3)),
        ("lab", expected_labs, (300, 4)),
        ("assessment", expected_assessments, (300, 4)),
    ):
        for entry in sorted(entries):
            path = ROOT / entry
            if path.is_file():
                problems.extend(check_text_resource(path, *floor, kind))

    # Every notebook that a module promises must be reachable in the site navigation.
    navigation = "\n".join(nav_entries())
    for entry in discovered:
        if entry not in navigation:
            problems.append(f"notebook is not in mkdocs.yml navigation: {entry}")
    library = (DOCS / "notebook-library.md").read_text(encoding="utf-8")
    for entry in discovered:
        if Path(entry).name not in library:
            problems.append(f"notebook is not linked from docs/notebook-library.md: {entry}")

    # A file that exists but is not linked is an orphan for the student. This is
    # the table-of-contents failure the link checker cannot see by itself.
    linked: set[Path] = set()
    link_re = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)>#\s]+)")
    for page in DOCS.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for match in link_re.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            linked.add((page.parent / target).resolve())
    for entry in sorted(expected_lessons | expected_labs | expected_assessments):
        path = ROOT / entry
        if path.is_file() and path.resolve() not in linked:
            problems.append(f"resource exists but is not linked from any Markdown page: {entry}")

    generated = {"outputs", "__pycache__", ".ipynb_checkpoints"}
    for directory in sorted(NOTEBOOKS.rglob("*")):
        if not directory.is_dir() or directory.name in generated:
            continue
        if not any(directory.glob("*.ipynb")):
            problems.append(f"notebook directory has no notebook: {directory.relative_to(ROOT)}")

    if problems:
        print(f"{len(problems)} course-inventory problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(build_inventory(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    standard = sum(entry in STANDARD_NOTEBOOKS for entry in discovered)
    print(
        f"ok: {len(MODULES)} modules, {len(expected_lessons)} module lesson files, "
        f"{len(discovered)} notebooks, {len(expected_labs)} labs/project briefs, "
        f"{len(expected_assessments)} assessments; {standard} notebooks meet the full "
        "14-section instructional standard"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
