# P11 - Video action recognition prototype

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Advanced |
| **Effort** | 50-65 hours |
| **Hardware** | CPU for the small synthetic clips; a GPU for real video |
| **Prerequisites** | [VD05 image models vs temporal models](../../lessons/video-ai/vd05-image-vs-temporal-models.md), [VD11 action recognition](../../lessons/video-ai/vd11-action-recognition.md), [VD12 video classification and events](../../lessons/video-ai/vd12-video-classification-and-events.md), [VD13 fine-tuning for video](../../lessons/video-ai/vd13-fine-tuning.md), [VD14 evaluation](../../lessons/video-ai/vd14-evaluation-and-deployment.md) |
| **Builds on** | Video AI lab 6 (frame versus temporal classifiers) |

## 1. Problem statement and motivation

A prototype that recognises a small set of actions in short clips - walking,
waving, sitting, standing up - is the entry point to activity monitoring, sports
analysis, and human-robot interaction. It is also the clearest demonstration of why
temporal information matters: a single frame of a person mid-stride looks like
standing, and a model that only sees frames will say so.

The course's synthetic default set uses five **movement** classes (`right`, `left`,
`approach`, `depart`, `stationary`) because they can be labelled exactly by the
generator. That is a deliberate substitute for human actions, not a claim that the
classes are equivalent: use your own consented clips if your goal is human activity.

This project compares a frame-based classifier with a temporal model on the same
clips, then asks the question most tutorials skip: does the clip-level label survive
when the clip is short, noisy, or viewed from a new angle?

**Decision supported:** a clip-level action label with confidence, for a human to
review. Not a real-time safety or surveillance decision.

## 2. Intended learning outcomes

1. Build a clip dataset with a documented label guide and a split by source clip.
2. Sample frames deliberately (uniform, dense, or keyframe) and justify the choice.
3. Train a frame-based classifier with temporal voting and a clip-level temporal model.
4. Evaluate at clip level, with per-class metrics, confusion, and temporal stability.
5. Test robustness to frame drop, shortened clips, and camera angle change.
6. Analyse where temporal context changes the answer, with examples.
7. State the privacy and consent position for any footage of people.

## 3. Difficulty and prerequisites

**Level:** Advanced. 50-65 hours: 10 data, 10 frame model, 12 temporal model, 14
evaluation, 8 robustness, 11 packaging and writing.

Requires VD05 and VD11-VD14. You should be able to explain what a 3D convolution or
a temporal pooling layer does before training one.

## 4. Scope and out-of-scope features

**In scope**

- 4-6 action classes, 30+ clips per class, 2-6 seconds each.
- Frame sampling policy and a frame-based baseline with voting.
- One temporal model (3D CNN, CNN+LSTM, or temporal pooling over frame features).
- Clip-level evaluation plus a stability measure across frames.
- Robustness: frame dropping, clip truncation, resized frames, and a held-out angle
  or background if you have one.
- A CLI that classifies one clip and prints top-k with confidence.

**Out of scope**

- Detecting *who* is acting, tracking identities, or recognising individuals.
- Real-time streaming, multi-camera fusion, or edge deployment.
- Action localisation in long untrimmed video (temporal proposals). If you attempt
  it, it needs its own evaluation and is an extension.
- Any use for surveillance, policing, or automated judgement of behaviour.
- Clips of people who have not consented, including scraped video.

## 5. Dataset options, licences, and preparation

| Option | Source | Licence | Notes |
| --- | --- | --- | --- |
| A (default, offline) | Synthetic action clips from `video_core.actions` (the module behind Video AI lab 6) | CC0-1.0, generated | 5 movement classes, clean and deterministic; not human actions |
| B | UCF101 or similar | Commonly research-only; check the dataset page | Strong results are possible but publication rights are restricted |
| C | Your own recordings | Consent from every person visible; no faces if avoidable | Best learning; 30 clips per class is a real weekend of work |

**Preparation**

1. Run `python projects/video-ai/lab6_action_recognition.py --selftest` to confirm the
   environment and see the five classes. Then export the synthetic clips to disk (or
   load them through the module) and record the generator seed. Confirm the class
   names match `synth.ACTION_CLASSES` rather than assuming human-action labels.
2. Write the label guide: one action per clip, what to do with transitions ("sitting
   down" vs "sitting"), and minimum clip length.
3. Split by source clip, stratified by class. A clip is never cut into pieces that
   land in different splits.
4. Record for each clip: fps, frame count, resolution, duration, class, source.
   Flag clips shorter than your sampling window.
5. For real footage, write the consent record: who appears, what they agreed to,
   where files are stored, deletion date.

**A note on the synthetic option:** the motions are simple and the backgrounds are
controlled. Accuracy on this set says nothing about accuracy on real video. Every
report must say that in the results section, not in a footnote.

## 6. Recommended baseline

**Frame-based classifier with majority vote.** Sample 8 frames uniformly, classify
each, take the majority. This is the baseline every temporal model must beat, and on
short simple clips it is surprisingly strong.

Second baseline: **single-frame model at the middle frame**, to show how much the
vote itself contributes. If the temporal model does not beat the vote, report that
honestly; it is a common and useful result.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Clip dataset and manifest | Counts, label guide, split audit | 10 |
| 2 | Frame baseline | Per-frame accuracy, vote accuracy | 10 |
| 3 | Temporal model | Clip accuracy, training curves | 12 |
| 4 | Evaluation | Per-class, confusion, stability | 10 |
| 5 | Robustness | Frame drop, truncation, resize, angle | 10 |
| 6 | Package | CLI, model card, report | 8 |

## 8. Repository or folder structure

```text
capstone-p11/
  README.md
  requirements.txt
  configs/
    train.yaml            # frames per clip, size, epochs, lr, sampling policy
  data/
    dataset-card.md
    label-guide.md
    manifest.csv          # clip, class, fps, frames, duration, split, consent
  src/
    clips.py              # decode, sample frames, uniform/dense policies
    frame_model.py        # per-frame classifier
    temporal_model.py     # clip classifier (3D CNN / CNN+LSTM / pooling)
    train.py
    evaluate.py           # clip metrics, stability, confusion
    robustness.py         # drop, truncate, resize, angle
    predict.py            # one clip -> top-k
  tests/
    test_clips.py
    test_sampling.py
    test_metrics.py
  reports/
    report.md
    model-card.md
  outputs/
    metrics.json
    per_class.csv
```

## 9. Detailed development tasks

1. `clips.py`: decode with a frame count check, sample frames according to policy,
   and return a tensor with shape documented. Assert that the number of frames
   returned matches the policy for clips longer than the window.
2. `test_sampling.py`: uniform sampling over 10 frames must return the expected
   indices; a clip shorter than the window must be padded or repeated by a stated
   rule, not silently truncated.
3. Frame model: small CNN on 64x64 frames, trained with class-balanced sampling.
   Report per-frame accuracy before voting.
4. Vote baseline: majority over 8 frames, ties broken by mean probability. Report
   the number of clips where the vote and the middle frame disagree.
5. Temporal model: choose one of (a) 3D CNN on stacked frames, (b) CNN features per
   frame followed by an LSTM or GRU, (c) temporal pooling with attention. Justify
   the parameter count against the dataset size.
6. Train with the same split and a fixed seed. Log clip-level validation accuracy
   per epoch and keep the best checkpoint.
7. `evaluate.py`: clip accuracy, macro F1, per-class precision/recall, confusion
   matrix, and top-2 accuracy. Report both models side by side.
8. Stability: for each test clip, compute the fraction of frames whose predicted
   class matches the clip prediction. Report the mean and the five least stable
   clips, with the frames that disagree.
9. Robustness: drop every second frame, truncate to the first 50% of the clip,
   downscale to 48x48, and (if available) evaluate on a held-out background or
   angle. Report the change in clip accuracy for both models.
10. Error analysis: 20 misclassified clips, categorised as ambiguous label, too
    short, motion similar to another class, occlusion, or model failure. Quote two
    per category where possible.
11. `predict.py`: `--clip path.mp4 --topk 3` prints class probabilities and a
    confidence flag below τ.
12. Model card: classes, data, accuracy, stability, failure modes, prohibited uses
    (surveillance, behaviour judgement, identity inference).

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| Sampling test | Policy is deterministic and correct | Expected indices for known lengths |
| Shape test | Tensors match model input | Assert shape for a 12-frame clip |
| Split test | No clip crosses splits | Intersection empty |
| Metric test | Clip accuracy is right | Hand case: 8 clips, 6 correct = 0.75 |
| Vote test | Ties are handled | Constructed tie resolves as documented |
| Reload test | Checkpoint works | 5 stored clips reproduce predictions |

Protocol: tune on validation, test once. Robustness results are reported as a
separate table and never used to pick the checkpoint.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| Clip accuracy and macro F1 | The user-facing number |
| Per-class precision and recall | Finds the weak action |
| Top-2 accuracy | Whether the answer is at least considered |
| Frame-vote agreement | How much temporal aggregation contributes |
| Mean frame stability | Whether predictions are coherent over time |
| Accuracy under frame drop, truncation, resize | Robustness |
| Inference time per clip | Prototype feasibility |

**Qualitative**

- Two clips where the temporal model is right and the frame model is wrong, and two
  where the reverse holds.
- Whether labels are distinguishable from a single frame at all.
- A statement about synthetic-versus-real transfer.

## 12. Expected deliverables

- [ ] Clip manifest with consent or licence record per clip.
- [ ] Label guide and split audit.
- [ ] Frame baseline, vote baseline, and temporal model results.
- [ ] Per-class table, confusion matrix, stability measure.
- [ ] Robustness table with four conditions.
- [ ] Error analysis with categories and quoted examples.
- [ ] CLI with top-k and confidence flag.
- [ ] Model card and report.
- [ ] Tests passing.

## 13. Suggested extensions

- Add temporal action localisation on a long clip with start/end predictions and a
  segment-level metric.
- Compare uniform sampling with dense sampling at equal compute.
- Add a two-stream (RGB + frame difference) model and report the gain.
- Evaluate on a small real dataset with a documented licence and report the
  synthetic-to-real gap.

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Temporal model no better than vote | Clips too short or classes distinguishable per frame | Report it; try harder classes or longer clips |
| Accuracy collapses when frames are dropped | Model depends on one specific frame | Sample more frames during training; use temporal pooling |
| All clips predicted as one class | Imbalance or learning rate | Class weights, lower LR, check per-class counts |
| Loss NaN | Learning rate too high for 3D convolutions | Lower LR, gradient clipping |
| Different results per run | Unseeded sampling or shuffling | Seed data order, sampling, and augmentation |
| Model uses background | Scene correlates with action | Test on a new background; augment backgrounds |
| Very slow on CPU | 3D CNN too large | Reduce frames, resolution, or channels; report the cost |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Dataset and labels | 15% | Manifest, consent, label guide, split audit | Documented dataset | Weak documentation | Unlicensed or leaking |
| Baselines | 15% | Frame, vote, and middle-frame baselines compared | Frame baseline present | One baseline | None |
| Temporal modelling | 20% | Justified architecture, matched compute, honest comparison | Temporal model trained | Attempted, not compared | No temporal model |
| Evaluation | 25% | Clip metrics, stability, robustness, error categories | Clip metrics and confusion | Accuracy only | Misleading |
| Ethics and communication | 15% | Consent, prohibited uses, synthetic-to-real caveat prominent | Limits stated | Thin | Overstated |
| Reproducibility | 10% | Config, seeds, one-command rerun | Minor manual steps | Undocumented | Cannot rerun |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 prototype works, analysis
thin; below 70 the action claim is unsupported.

## 16. Self-review checklist

- [ ] Every clip has consent or a licence record.
- [ ] Splits are by clip, not by frame.
- [ ] Frame, vote, and temporal results are in one table.
- [ ] Stability across frames is measured.
- [ ] Four robustness conditions are reported.
- [ ] Error analysis is categorised with examples.
- [ ] The synthetic-to-real caveat is in the results section.
- [ ] Prohibited uses are listed.
- [ ] No footage of identifiable people is committed.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Data and consent** - classes, clip counts, source, permissions.
2. **Temporal design** - sampling policy, architecture, parameter budget.
3. **Results** - frame vs vote vs temporal, per class, stability.
4. **Robustness** - four conditions and the interpretation.
5. **Limits** - synthetic data, short clips, no localisation.

## 18. Demonstration and presentation checklist

- [ ] Classify three clips: two clear, one ambiguous.
- [ ] Show the same clip through frame, vote, and temporal models.
- [ ] Show a stability plot or table for one clip.
- [ ] Show the frame-drop result.
- [ ] State the consent position and prohibited uses.
- [ ] Answer: "What would it take to run this on a live camera?"

**Demo trap:** choosing clips that are all the same action type. Mix them.

---

**Previous:** [P10 garment attributes](p10-garment-attributes.md) · **Next:** [P12 tool-using agent](p12-tool-using-agent.md) · [Index](index.md)
