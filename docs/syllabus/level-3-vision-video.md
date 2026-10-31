# Level 3 - Vision, speech, and video AI

**Modules:** M11-M14 | **Hours:** 82 | **Hardware:** GPU recommended to GPU required

Level 3 applies the foundations to images, audio, and video. You will train image
classifiers, detect and track objects, build speech and audio systems, and create
a privacy-preserving video analytics prototype.

!!! note "Level outcome"
    You can adapt vision, speech, and video models to a new domain, evaluate them
    with modality-appropriate metrics, and document the privacy and licensing
    constraints that apply.

## Readiness check

- Can you fine-tune a pretrained model and evaluate it on held-out data?
- Can you build a class-balanced evaluation and analyze error slices?
- Do you have GPU access for detection and video experiments?
- Can you write a dataset card with license and privacy notes?

If not, complete Level 1 and M05 first.

---

## M11 - Image classification and computer vision {#m11}

**Level 3 | 18 hours | GPU recommended | Prerequisite: M04, M05**

### Learning objectives

By the end of this module, you can:

1. Explain image representation, normalization, and augmentation semantics.
2. Fine-tune a CNN or vision transformer on a new image dataset.
3. Compare linear probing, partial fine-tuning, and full fine-tuning.
4. Evaluate with per-class metrics, calibration, and slice analysis.
5. Use Grad-CAM or a comparable method to inspect model attention.
6. Diagnose dataset bias, background shortcuts, and label noise.
7. Package an image classifier for a simple demo.

### Prerequisites

- M04 (training from scratch).
- M05 (dataset preparation).
- GPU recommended; CPU inference is sufficient for the demo.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 3 h | 7 h | 7 h | 1 h | 18 h |

### Required theory

- Pixels, channels, resolution, color spaces, and normalization.
- Image augmentation: flips, crops, color jitter, rotation, and their label
  assumptions.
- CNN feature hierarchies and residual networks.
- Transfer learning: linear probe, partial unfreeze, full fine-tuning.
- Vision transformers and patch embeddings (conceptual).
- Class imbalance, long tails, and macro vs micro metrics.
- Calibration and confidence reliability.
- Grad-CAM and attention visualization.
- Shortcut learning: background, watermark, and source leakage.
- Deployment: input validation, preprocessing parity, and batch inference.

### Guided notebook

**Planned path:** `notebooks/computer-vision/m11_image_classification.ipynb`

The notebook will:

1. Build an image dataset with a documented split.
2. Fine-tune a small pretrained CNN on a 10-class public dataset.
3. Compare a frozen backbone, partial fine-tuning, and full fine-tuning.
4. Evaluate per-class precision, recall, macro F1, and calibration.
5. Inspect misclassified and high-confidence wrong examples.
6. Generate Grad-CAM overlays for correct and incorrect predictions.
7. Export the model and run inference on a new image.

**Dataset:** Oxford-IIIT Pet, Food-101 subset, or another licensed 10-class
dataset. Verify the current terms before redistribution.

**Hardware:** GPU recommended for fine-tuning; CPU works for inference.

### Independent lab

**Brief:** Build a domain image classifier with at least five classes and 300 or
more labeled images.

Required evidence:

- Dataset card with license, source, and collection method.
- Labeling guideline and sample review.
- Train/validation/test splits with duplicate checks.
- Baseline and at least two transfer-learning strategies.
- Macro F1, per-class precision/recall, confusion matrix, and calibration.
- Error slices by lighting, background, source, or class.
- Grad-CAM or attention examples with interpretation.
- A demo with confidence display and an "unknown" threshold.
- A deployment note on preprocessing parity.

**Constraints:** No personal images without consent. No scraped data that
violates terms. Do not report only aggregate accuracy.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- The test split is untouched until final evaluation.
- Per-class metrics reveal weak classes.
- Calibration or confidence analysis is present.
- At least one shortcut or bias is investigated.

### Deliverables

- Executed notebook.
- Dataset card and labeling guide.
- Classifier demo.
- Evaluation report with visual error analysis.
- Model card.

### Next step

M12 - Object detection, tracking, and transfer learning.

### Risks and notes

- **Background shortcuts:** a model may learn the source, not the object.
- **Duplicate images** across splits inflate accuracy.
- **Preprocessing mismatch** between training and demo is a common deployment
  bug.
- **Licensing:** image datasets often have per-image terms; check before
  redistribution.

---

## M12 - Object detection, tracking, and transfer learning {#m12}

**Level 3 | 20 hours | GPU required for training | Prerequisite: M11**

### Learning objectives

By the end of this module, you can:

1. Explain bounding boxes, annotation formats, IoU, and non-maximum suppression.
2. Compare anchor-based, anchor-free, and transformer-based detectors.
3. Prepare a detection dataset in COCO or YOLO format and validate it.
4. Fine-tune a small detector with transfer learning.
5. Evaluate with mAP at multiple IoU thresholds and per-class results.
6. Build a multi-object tracking pipeline with stable IDs.
7. Analyze tracking failures such as identity switches and occlusions.
8. Export a model for efficient inference and document its license.

### Prerequisites

- M11.
- M05.
- GPU access for training.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 3 h | 8 h | 8 h | 1 h | 20 h |

### Required theory

- Bounding boxes, coordinates, normalization, and format conversion.
- Intersection over Union and non-maximum suppression.
- Anchor-based detectors, anchor-free detectors, and DETR-style transformers.
- Backbone, neck, and head; feature pyramids.
- Detection losses: classification, localization, and objectness.
- Mean average precision and per-class evaluation.
- Annotation quality and missing-label problems.
- Small-object detection and image resolution trade-offs.
- Multi-object tracking: detection association, Kalman filters, Hungarian
  matching, and ByteTrack.
- Tracking metrics and identity switches.
- Model export: ONNX, TensorRT, and edge constraints.
- Licensing: some popular detector implementations use AGPL; choose deliberately.

### Guided notebook

**Planned path:** `notebooks/computer-vision/m12_detection_tracking.ipynb`

The notebook will:

1. Load a licensed 200-500 image detection subset in COCO format.
2. Validate boxes, classes, and split integrity.
3. Fine-tune a small detector for a few epochs.
4. Evaluate mAP@0.5 and mAP@0.5:0.95 with per-class results.
5. Run inference on a short video clip.
6. Track detections with ByteTrack and assign stable IDs.
7. Visualize trajectories and count line crossings.
8. Analyze at least five failure cases.

**Dataset:** a licensed COCO subset, a course-provided clip, or a small custom
dataset. Verify licenses and do not commit media.

**Hardware:** GPU required for training. Inference on short clips can run on CPU
with a small model.

### Independent lab

**Brief:** Build a detection and tracking pipeline for a legitimate task, such as
vehicle counting, wildlife monitoring, or retail shelf auditing.

Required evidence:

- Dataset card and annotation guideline.
- Format conversion and validation report.
- Baseline detector and fine-tuned detector comparison.
- mAP overall and per class.
- Tracking results with ID stability and failure cases.
- Task metric, such as counting error or zone-entry accuracy.
- Inference speed and hardware.
- License analysis for the detector implementation and weights.
- Privacy note if the footage contains people.

**Constraints:** No face recognition or identity inference. No covert
surveillance. Use public, licensed, or consented footage. Blur faces and plates
when they are not needed for the task.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- Annotation format and split integrity are validated.
- mAP is reported with per-class results.
- Tracking failures are analyzed, not hidden.
- The detector license is compatible with the intended use.

### Deliverables

- Detection and tracking notebook or app.
- Annotation and dataset documentation.
- mAP and tracking evaluation report.
- Short demo clip with overlays.
- License and privacy note.

### Next step

M13 - Speech recognition, audio classification, and speech generation, or M14 -
Video understanding and analytics.

### Risks and notes

- **AGPL detectors:** Ultralytics YOLO is AGPL-3.0. It is fine for learning, but
  distribution or commercial use may require a license. Permissive alternatives
  include torchvision detectors and RT-DETR implementations; verify each.
- **mAP can hide weak classes.** Always report per-class results.
- **Tracking is not detection.** Identity switches need separate analysis.
- **Small objects** require higher resolution, which costs memory and speed.

---

## M13 - Speech recognition, audio classification, and speech generation {#m13}

**Level 3 | 22 hours | GPU recommended | Prerequisite: M03, M05**

### Learning objectives

By the end of this module, you can:

1. Explain waveforms, sample rates, STFT, mel spectrograms, and MFCCs.
2. Run and evaluate an automatic speech recognition (ASR) model.
3. Explain CTC and attention-based sequence-to-sequence ASR at a high level.
4. Fine-tune or adapt a small ASR model to a domain or accent.
5. Train or adapt an audio classifier for environmental or domain sounds.
6. Generate speech with an open TTS model and evaluate intelligibility.
7. Evaluate with WER, CER, confusion analysis, and listening tests.
8. Document consent, privacy, and licensing for voice data.

### Prerequisites

- M03.
- M05.
- Basic signal processing is helpful but not required.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 4 h | 8 h | 9 h | 1 h | 22 h |

### Required theory

- Waveforms, sampling, quantization, and Nyquist limit.
- Audio loading, resampling, mono conversion, and normalization.
- STFT, spectrograms, mel scale, and MFCCs.
- ASR pipeline: features, acoustic model, decoder, language model.
- CTC, attention encoder-decoder, and Whisper's approach.
- Word error rate, character error rate, and normalization rules.
- Domain shift: noise, accent, microphone, and speaking rate.
- Audio classification with CNNs and transformers.
- TTS pipeline: text normalization, acoustic model, vocoder.
- Speech generation risks: consent, voice cloning, and impersonation.
- Evaluation: WER/CER by slice, classification F1, and listening tests.
- Dataset and model licenses, especially non-commercial research datasets.

### Guided notebook

**Planned path:** `notebooks/speech-audio/m13_speech_audio.ipynb`

The notebook will:

1. Load and inspect audio: sample rate, duration, waveform, spectrogram.
2. Run a small Whisper model on a few clips and compute WER/CER.
3. Fine-tune or adapt a small ASR model on a tiny licensed dataset.
4. Train an audio classifier on a subset of Speech Commands.
5. Evaluate per-class performance and confusion.
6. Generate speech with a small open TTS system.
7. Run a short listening test and record intelligibility notes.

**Datasets:** LibriSpeech or Common Voice for ASR; Speech Commands for audio
classification. Check licenses; some audio datasets are non-commercial.

**Hardware:** GPU recommended for fine-tuning. Whisper tiny/base inference is
feasible on CPU for short clips.

### Independent lab

**Brief:** Build a speech or audio system for a bounded domain and evaluate it by
condition.

Choose one:

- **ASR adaptation:** adapt a small Whisper model to a domain or accent and
  compare base vs adapted WER by noise and speaker group.
- **Audio classification:** build a 5-10 class sound classifier and evaluate
  under background noise.
- **Speech interface:** combine ASR, a simple command parser, and TTS.

Required evidence:

- Dataset card with consent and license.
- Audio preprocessing and normalization policy.
- Baseline and adapted model comparison.
- WER/CER or classification metrics by condition.
- Confusion analysis with audio examples.
- Latency and model size.
- Privacy and consent statement.

**Constraints:** No voice cloning without explicit consent. No personal recordings
without permission. Do not redistribute non-commercial datasets.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- Text normalization rules are stated before computing WER.
- Metrics are broken down by noise, accent, or speaker condition.
- Audio data consent and license are documented.
- Generated speech is evaluated for intelligibility, not just produced.

### Deliverables

- Executed notebook.
- Dataset card and consent statement.
- ASR or audio classifier with evaluation by condition.
- TTS demo if applicable.
- Short report on failure modes.

### Next step

M14 - Video understanding and video analytics.

### Risks and notes

- **Non-commercial datasets:** ESC-50 and UrbanSound8K have restrictions. Read
  the license before any deployment.
- **Voice cloning:** excluded without explicit, documented consent. Do not build
  impersonation tools.
- **WER depends on normalization.** Compare systems with the same text
  normalization.
- **Audio privacy:** voices can identify people; minimize retention and access.

---

## M14 - Video understanding and video analytics {#m14}

**Level 3 | 22 hours | GPU recommended | Prerequisite: M12, M13 (M12 minimum)**

### Learning objectives

By the end of this module, you can:

1. Represent video as frames, clips, and audio with correct temporal sampling.
2. Explain 2D CNN + temporal pooling, 3D CNNs, and video transformers.
3. Run and evaluate an action-recognition model on a small dataset.
4. Build a detection and tracking pipeline for video analytics.
5. Add temporal smoothing and zone or line-crossing logic.
6. Evaluate counting, tracking, and attribute classification with task metrics.
7. Design a privacy-preserving pipeline with blurring, retention, and access
   controls.
8. Document purpose limitation, consent, and dataset licensing.

### Prerequisites

- M12 (detection and tracking).
- M13 is helpful for audio but not mandatory.
- GPU recommended.

### Study time

| Theory | Guided notebook | Lab | Assessment | Total |
| --- | --- | --- | --- | --- |
| 4 h | 8 h | 9 h | 1 h | 22 h |

### Required theory

- Video structure: frame rate, resolution, codecs, and audio tracks.
- Frame sampling, clip length, and temporal stride.
- 2D CNN with temporal aggregation.
- 3D convolutions and inflated 3D models.
- Video transformers and spatiotemporal attention.
- Action recognition datasets and label ambiguity.
- Detection plus tracking for analytics.
- Temporal smoothing, hysteresis, and zone logic.
- Vehicle analytics: type, direction, counts, and trajectories.
- Clothing attribute recognition for retail cataloging and robotics.
- Edge deployment: throughput, batching, and hardware acceleration.
- Privacy: purpose limitation, data minimization, blurring, retention, and
  access control.
- Legal and ethical boundaries: no face recognition, no identity inference, no
  covert surveillance.

### Guided notebook

**Planned path:** `notebooks/video-ai/m14_video_analytics.ipynb`

The notebook will:

1. Decode a short licensed clip and inspect frame rate and resolution.
2. Sample frames and build clips for an action-recognition model.
3. Run inference with a small pretrained video model.
4. Compare frame sampling rates and their effect on accuracy and speed.
5. Run detection and tracking on a traffic or retail clip.
6. Add zone or line-crossing counts.
7. Blur faces and plates before saving outputs.
8. Measure processing FPS and identify bottlenecks.

**Data:** UCF101 subset for action recognition, plus a short CC-licensed or
course-provided clip for analytics. Verify all licenses; do not commit videos.

**Hardware:** GPU recommended. CPU works for short clips at reduced resolution.

### Independent lab

**Brief:** Build a privacy-preserving video analytics prototype for one bounded
task:

- Vehicle type and direction counting on public traffic footage.
- Occupancy or queue measurement in a consented retail or service setting.
- Clothing attribute classification on licensed catalog images or consented
  footage for retail or robotics.

Required evidence:

- Purpose statement, users, and explicit non-goals.
- Dataset or footage card with license and consent.
- Detection and tracking pipeline description.
- Task metric: counting MAE, zone accuracy, or attribute macro F1.
- Tracking quality and failure analysis at occlusion and low light.
- Processing FPS and hardware.
- Privacy impact assessment: what is collected, blurred, stored, and retained.
- Access control and retention policy.
- A demonstration that faces and plates are not stored unblurred.
- A statement that no identity recognition is performed.

**Constraints:** No face recognition. No re-identification of people. No inference
of sensitive attributes. No covert recording. Public, licensed, or explicitly
consented footage only. Purpose limitation and deletion must be documented.

### Assessment criteria

Module score: knowledge check 20%, guided notebook 30%, lab 40%, reflection 10%.
The lab uses the [standard rubric](../course/assessments.md#lab-rubric).

Module-specific must-haves:

- The task has a documented legitimate purpose and non-goals.
- Privacy controls are implemented, not just described.
- The task metric is evaluated, not only demonstrated.
- Failure analysis covers occlusion, lighting, and tracking errors.

### Deliverables

- Video analytics prototype.
- Task evaluation report.
- Privacy impact assessment and retention policy.
- Demo clip with blurring.
- Model and dataset cards.

### Next step

M15 - AI agents, tool calling, memory, and workflows.

### Risks and notes

- **Surveillance risk:** video analytics can cause real harm. If the purpose is
  not clearly legitimate, stop and consult the instructor.
- **Dataset licenses:** video datasets often restrict commercial use and
  redistribution.
- **Temporal smoothing** can hide errors; report raw and smoothed metrics.
- **Edge constraints:** accuracy at 30 FPS may be worse than offline accuracy.

---

## Level 3 completion checklist

- [ ] I can fine-tune and evaluate an image classifier with calibration.
- [ ] I can train a detector and report per-class mAP.
- [ ] I can build a tracking pipeline and analyze identity failures.
- [ ] I can evaluate ASR with WER by condition.
- [ ] I can train or adapt an audio classifier.
- [ ] I can build a video analytics prototype with privacy controls.
- [ ] I can document licenses, consent, and limitations for visual and audio data.
- [ ] I have portfolio artifacts for M11-M14.

Proceed to [Level 4 - AI agents](level-4-agents.md).
