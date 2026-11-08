# CV14 - Evaluation, robustness, and deployment {#cv14}

**Section path:** [Overview](index.md) · **Module 14** · [Assessment](assessment.md) · [Model card](model-card.md)

| | |
| --- | --- |
| **Study time** | 5 hours: 2 h reading, 3 h practice |
| **Hardware** | CPU-only |
| **Prerequisites** | CV05-CV13 |
| **You will produce** | A robustness table, a calibration number, three labelled error cases, and a complete model card |

## Why this module exists

Everything before this module measured a model on the data it was trained for. Deployment
is a different distribution, a different threshold, and a different set of consequences.
This module is the checklist that turns "it works" into "here is the evidence, here is
what it fails on, and here is who should not use it".

## Accuracy is one number; these are the others

| Question | Metric | Where |
| --- | --- | --- |
| Is it right on clean data? | accuracy / mAP / mIoU | CV05, CV09, CV10 |
| Is it right when input quality drops? | accuracy per perturbation | `evaluation.robustness_suite` |
| Can I trust its confidence? | expected calibration error | `metrics.expected_calibration_error` |
| Where does it fail, specifically? | error cases with inputs | `evaluation.error_analysis` |
| Is it fast enough? | median / p90 latency | CV13 |
| Should it be deployed at all? | model card + review | this module |

## Robustness: perturb, then report

```python
report = evaluation.robustness_suite(model, test_images, test_labels, mean, std)
print(evaluation.format_robustness(report))
```

Seven conditions: clean, brightness up, brightness down, Gaussian noise, blur, JPEG
quality 30, 25% occlusion. Measured on Lab 4's fine-tuned object classifier:

| Condition | Accuracy | Change |
| --- | --- | --- |
| clean | 0.500 | - |
| brightness 1.3x | 0.500 | +0.000 |
| brightness 0.7x | 0.500 | +0.000 |
| gaussian noise 0.08 | 0.611 | +0.111 |
| blur radius 1.2 | 0.500 | +0.000 |
| jpeg quality 30 | 0.500 | +0.000 |
| occlusion 25% | 0.667 | +0.167 |

The honest reading: a model at 0.500 on 18 test images has nowhere to fall, and the
"improvements" are single-image noise. The table is still required - it is how you discover
that a model is insensitive to the perturbations you tested, which is *not* the same as
being robust.

!!! warning "Robustness testing is not a certificate"
    These perturbations are the ones you thought of. They do not cover lighting
    temperature, motion blur, rain, sensor noise, compression by a specific app, or the
    distribution shift of a new camera. Report what you tested and what you did not.

## Calibration: does 0.9 mean 90%?

A model that is right 70% of the time when it says 0.9 is overconfident, and any
threshold-based decision inherits that error.

```python
ece = metrics.expected_calibration_error(confidences, correct, n_bins=10)
```

ECE is the weighted average gap between confidence and accuracy across bins. 0.0 is
perfect; above ~0.1 on a small test set, treat confidence scores as ordinal, not
probabilities. Temperature scaling on a validation split is the standard fix and takes
about ten lines - the section does not implement it, and says so.

## Error analysis: three cases, not a number

```python
cases = evaluation.error_analysis(model, images, labels, class_names, mean, std, k=5)
```

For each case, record: the image, the true label, the prediction, the confidence, and a
one-line hypothesis. Then group the hypotheses. In this section's object task, the
recurring causes are:

1. **Class pairs with similar geometry** (square vs book) - a data/definition problem.
2. **Low-contrast instances** - augmentation could cover it.
3. **Occluded instances** - the label says "present", the pixels disagree.

Grouping matters more than counting: three cases with one cause is one fix, not three.

## Model cards

`projects/computer-vision/vision_core/cards.py` holds the template; Lab 4 writes one:

```text
outputs/lab4_model_card.md    complete=True    missing=[]
```

A card that a reviewer can use answers:

| Field | What "good" looks like |
| --- | --- |
| Intended use | a specific task, user, and setting |
| Out of scope | the uses you know are wrong, stated plainly |
| Training data | source, licence, size, known gaps |
| Metrics | value + dataset + sample size + threshold |
| Failure modes | measured, with the group or condition affected |
| Limitations | what the evaluation did not cover |
| Contact / version | who owns it, which commit produced it |

"Trained on a large dataset, achieves high accuracy" is a card that says nothing. The full
template with instructions is on the [model card page](model-card.md).

## Deployment checklist

Before a vision model faces users:

- [ ] Test split grouped by source; leakage audit clean or explained
- [ ] Metrics reported per class **and** per group that matters (lighting, tone, camera)
- [ ] Threshold chosen from the cost of FP vs FN, written down with the reasoning
- [ ] Robustness table produced, including conditions you expect in deployment
- [ ] Latency measured on the deployment hardware at the deployment input size
- [ ] Model card complete, including out-of-scope uses
- [ ] Input validation: wrong shape, wrong channel order, corrupt file all handled
- [ ] Logging of inputs/decisions with retention and access rules
- [ ] A human review path for consequential decisions
- [ ] Rollback plan: previous model version, previous threshold, and who can revert

## Monitoring after deployment

Models do not stay valid. Monitor:

- input distribution drift (mean brightness, blur metric, resolution),
- prediction distribution (class frequencies, score histogram),
- disagreement with human review, sampled weekly,
- latency p90 and error rate.

Alert on *change*, not only on absolute thresholds: the day the score histogram shifts is
the day the camera, the lighting, or the population changed.

## Practice

1. Run the robustness suite on your Lab 4 model and tabulate the result.
2. Compute ECE. Bin the confidences and say which bin is worst.
3. Produce three error cases with hypotheses, then group them.
4. Complete the model card. Every field you cannot fill is a finding.
5. Write the deployment checklist for a specific product (for example, a recycling
   sorting camera) and mark every item you cannot yet tick.

## Check yourself

1. Why is "accuracy unchanged under perturbation" not evidence of robustness at 0.500?
2. Your ECE is 0.14. What decision changes, and what is the cheapest fix?
3. Name three items on the deployment checklist that no amount of model training can satisfy.

## Where to go next

The section's capstone is the [assessment](assessment.md): a vision system of your own,
with a grouped split, measured metrics, an error analysis, a robustness table, and a model
card. Speech and video build directly on CV08-CV13.
