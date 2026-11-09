# Datasets and Resources

This page is the student entry point for data, pretrained models, hardware, and
the licence rules that apply to each. It describes what the repository actually
contains and what the course expects you to download or generate.

## The short version

- **Core exercises need no dataset download.** Foundations use four small
  synthetic tables committed under `datasets/foundations/`. The applied sections
  generate their own synthetic data with scripts in the repository.
- **Generated data is not committed.** Directories under `data/` and
  `projects/*/data/` are git-ignored; rerun the generator to restore them.
- **Pretrained weights are never committed.** Libraries download or cache them
  on your machine. Check the model card and licence before redistributing a
  weight file.
- **No paid API is required.** Optional hosted-model paths are labelled and can
  be skipped.

## Data used by the course

| Area | What it is | Where it comes from | Licence | Committed? |
| --- | --- | --- | --- | --- |
| Foundations (F01-F13) | Four small synthetic tables: house prices, student records, a messy customer table, and customer segments | [`scripts/make_foundation_data.py`](https://github.com/nadeem-majeedch/AITopics/blob/release/v0.1.0-rc.1/scripts/make_foundation_data.py); files in `datasets/foundations/` | CC0-1.0 | Yes, the CSV files and manifest |
| Small-language-model training (M06-M08) | Synthetic FAQ and instruction corpora, tiny text corpus, split manifests | [`scripts/make_training_data.py`](https://github.com/nadeem-majeedch/AITopics/blob/release/v0.1.0-rc.1/scripts/make_training_data.py); output in `datasets/training/generated/` | CC0-1.0 | Yes, the generated training fixtures |
| Chatbots and RAG (M09-M10) | Synthetic support corpus, adversarial notes, development and test questions | [`scripts/make_chatbot_data.py`](https://github.com/nadeem-majeedch/AITopics/blob/release/v0.1.0-rc.1/scripts/make_chatbot_data.py); output in `data/chatbots-rag/` | CC0-1.0 | No; regenerable |
| Computer vision (M11-M12) | Rendered shapes, objects, detection annotations, segmentation masks, synthetic faces | [`scripts/make_vision_data.py`](https://github.com/nadeem-majeedch/AITopics/blob/release/v0.1.0-rc.1/scripts/make_vision_data.py); output in `data/computer-vision/` | CC0-1.0 | No; regenerable |
| Speech and audio (M13) | Synthetic environmental sounds, spoken-style audio, diarization clip, leakage probes | [`scripts/make_audio_data.py`](https://github.com/nadeem-majeedch/AITopics/blob/release/v0.1.0-rc.1/scripts/make_audio_data.py); output in `data/audio/` | CC0-1.0 | No; regenerable |
| Video AI (M14) | Seven six-second rendered traffic clips with frame-exact boxes, track IDs, and counting lines | [`projects/video-ai/scripts/make_video_data.py`](https://github.com/nadeem-majeedch/AITopics/blob/release/v0.1.0-rc.1/projects/video-ai/scripts/make_video_data.py); output in `projects/video-ai/data/video/` | CC0-1.0 | No; regenerable |
| AI agents (M15) | Synthetic sales tables, policy corpus, safe and untrusted notes, task sets | [`scripts/make_agent_data.py`](https://github.com/nadeem-majeedch/AITopics/blob/release/v0.1.0-rc.1/scripts/make_agent_data.py); output in `data/agents/` | CC0-1.0 | No; regenerable |
| Evaluation and production (M16) | Synthetic support corpus, drift tables, detector predictions, adversarial cases | [`scripts/make_eval_data.py`](https://github.com/nadeem-majeedch/AITopics/blob/release/v0.1.0-rc.1/scripts/make_eval_data.py); output in `data/production/` | CC0-1.0 | No; regenerable |
| Capstone (M17) | Synthetic support tickets and instruction pairs with leakage checks | [`scripts/make_capstone_data.py`](https://github.com/nadeem-majeedch/AITopics/blob/release/v0.1.0-rc.1/scripts/make_capstone_data.py); output in `data/capstones/` | CC0-1.0 | No; regenerable |

Every generator uses fixed seeds and writes a manifest or dataset card. Re-running
a generator should produce the same content; if it does not, record the
difference before using the data in an assessment.

### Regenerate the data

Run these from the repository root, in a working virtual environment:

```bash
python scripts/make_foundation_data.py
python scripts/make_training_data.py
python scripts/make_chatbot_data.py
python scripts/make_vision_data.py
python scripts/make_audio_data.py
python scripts/make_agent_data.py
python scripts/make_eval_data.py
python scripts/make_capstone_data.py
python projects/video-ai/scripts/make_video_data.py
```

Some generators need the section requirements (for example OpenCV for vision and
video, or audio libraries for speech). Install only the requirements for the
section you are studying. The [foundation assets page](../technical/foundation-assets.md)
lists the foundation commands and expected files.

### Using your own data

You may substitute your own data in a lab when the brief allows it. Before you do:

1. Record the source, collection date, and permission or licence.
2. Remove personal identifiers you do not need.
3. Document the split rule before training, not after seeing test results.
4. Write a dataset card with intended use, limitations, and known gaps.
5. Do not commit restricted data; keep it outside the repository or in a local,
   ignored directory.

The [licensing and attribution register](../technical/licensing-and-attribution.md)
and [third-party inventory](../technical/third-party-inventory.md) record the
repository's own evidence. They do not grant you rights to a dataset you found
elsewhere.

## Pretrained models and libraries

The course uses open-source libraries rather than shipping model weights:

| Need | Typical source | What to check |
| --- | --- | --- |
| Classical ML | scikit-learn | BSD-3-Clause; no downloaded weights |
| Neural networks, CNNs, tiny language models | PyTorch | BSD-style licence; check the wheel and CUDA compatibility |
| Transformers and small language models | Hugging Face Transformers | Model card, base-model licence, and dataset terms are separate |
| Object detection | torchvision or Ultralytics YOLO | Code and weight licences can differ; Ultralytics has commercial terms |
| Speech recognition | OpenAI Whisper or faster-whisper | Check the model card and weight licence |
| Vector search | NumPy or a local vector index | Prefer a CPU baseline before adding a service |

Never commit a downloaded checkpoint, token, or API key. Cache weights outside
the repository or in an ignored directory. The repository's
[third-party licensing inventory](../technical/third-party-inventory.md) explains
which dependencies are audited and which terms remain unresolved.

## Hardware guide

| Setup | What works | What to expect |
| --- | --- | --- |
| Laptop CPU, 8-16 GB RAM | Levels 0-1, data work, RAG, small-model inference, agents, evaluation | The core path is designed to run without a GPU; training is slow but bounded |
| Free Colab or Kaggle GPU | Fine-tuning, detection, speech, and video labs | Session and quota limits; save artifacts before disconnect |
| Local NVIDIA GPU, 8 GB+ VRAM | Full training path with fewer interruptions | Driver, CUDA, and wheel compatibility matter; M01 teaches the check |

Each lesson, notebook, and lab states whether it is CPU-only, GPU recommended,
or GPU required. If a lab says GPU required, the CPU fallback is usually a
smaller demonstration, not an equivalent experiment. Report which path you ran.

## Where to go next

- New to the course? Start with [F01 - Python essentials](../lessons/f01-python-ai/index.md).
- Need the environment check? Open [F02 - Environments and Jupyter](../lessons/m01-environment/index.md).
- Looking for a notebook? Browse the [Notebook Library](../notebook-library.md).
- Stuck on an install? Read [Troubleshooting](../technical/troubleshooting.md).
- Need a policy answer? Read the [FAQ](../course/faq.md) and
  [licensing and attribution](../technical/licensing-and-attribution.md).
