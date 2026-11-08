# Assessment - Computer vision {#assessment}

**Section path:** [Overview](index.md) · **Assessment**

Eight labs worth 90%, plus a documented capstone worth 10%. Every mark is tied to a
measurement you can reproduce with one command, not to prose quality alone.

## Weights

| Item | Weight | Deliverable |
| --- | --- | --- |
| [Lab 1](labs/lab1-licensed-dataset-classifier.md) - dataset, splits, licence | 8% | split report, audit, licence block |
| [Lab 2](labs/lab2-cnn-learning-curves.md) - CNN and learning curves | 10% | curves, history, variant comparison |
| [Lab 3](labs/lab3-scratch-vs-transfer.md) - scratch vs transfer | 12% | three conditions with parameter counts |
| [Lab 4](labs/lab4-finetune-everyday-objects.md) - fine-tune and document | 12% | checkpoint, robustness table, model card |
| [Lab 5](labs/lab5-annotate-and-train-detector.md) - annotate and train a detector | 15% | audit, YOLO labels, mAP, failure analysis |
| [Lab 6](labs/lab6-detector-thresholds.md) - threshold sweep | 10% | sweep table, chosen threshold, cost reasoning |
| [Lab 7](labs/lab7-similarity-app.md) - similarity application | 10% | index, ranked queries, precision@k for two embeddings |
| [Lab 8](labs/lab8-deployment-comparison.md) - latency and size | 13% | four tables, recommendation, rejected optimisation |
| Capstone - documented model | 10% | model card + error analysis + reproduction command |

Face exercises ([CV11](cv11-face-detection-vs-recognition.md), [face page](faces.md)) are
graded inside Lab 4's documentation requirement and the capstone's ethical section; the
stratified analysis is a required element, not an optional extra.

## Grading bands

| Band | Mark | Descriptor |
| --- | --- | --- |
| Excellent | 85-100 | Every number reproducible; interpretation explains mechanism; limitations stated before they are asked for; one experiment beyond the brief |
| Good | 70-84 | Correct results, clear write-up, limitations mentioned but thin |
| Pass | 50-69 | Runs and reports numbers, but interprets weakly or omits sample sizes and thresholds |
| Fail | < 50 | Numbers not reproducible, split leaks, metrics mismatched to task, or tables copied from the manual |

## What every submission must contain

1. **A reproduction command** that regenerates the headline number.
2. **Sample sizes and thresholds** next to every metric. "0.933" is not a result; "0.933
   on 45 held-out images, grouped split, threshold 0.5" is.
3. **A limitation** you found yourself, with the measurement that showed it.
4. **A run log** from your machine, not the manual's output. Your hardware will produce
   different milliseconds; that is expected and must be reported.

## Academic integrity

- Report your own measurements. Copying the manual's numbers when your run differs is
  fabrication; grading is on interpretation, and mismatched numbers are visible.
- You may discuss approaches, but the code and write-up are yours.
- Any external dataset, pretrained weight, or library must be cited with its licence.
- Never use a face image of a real person without written consent, in any submission,
  including screenshots and demos. Synthetic faces are provided for this reason.

## Capstone: a documented vision system

Choose one task you can evaluate honestly in the time available. Suggested scope:

| Option | Task | Metric | Evidence required |
| --- | --- | --- | --- |
| A | Four-class object classifier on your own consented photos | accuracy + per-class | grouped split, robustness table |
| B | Detector for one object on 80+ annotated images | mAP@0.5 + threshold choice | audit, YOLO labels, precision/recall |
| C | Segmentation of two classes on 60+ masks | mIoU + per-class IoU | control baseline, boundary F1 |
| D | Similarity search over a labelled catalogue | precision@5, 1-NN | two embeddings compared |

Required sections:

```text
capstone/
  README.md            # task, data, licence, reproduction command
  data/                # or a manifest with hashes and a download/generation script
  train.py             # one command reproduces the model
  evaluate.py          # produces every number in the report
  results.md           # metrics with N, threshold, and per-class/per-group breakdown
  errors.md            # three error cases with hypotheses, grouped by cause
  model_card.md        # complete, cards.check_card returns complete=True
  reflection.md        # 300 words: what you would do with twice the time, and what you would not ship
```

### Capstone rubric

| Criterion | Marks |
| --- | --- |
| Problem framed with a metric that matches the task | 15 |
| Data provenance, licence, and a leak-free split | 20 |
| Working code, reproducible by one command | 20 |
| Metrics complete (N, threshold, per-class, stratified where relevant) | 20 |
| Error analysis with grouped causes | 15 |
| Model card complete and honest, including out-of-scope uses | 10 |

## Resubmission

Labs 1-8 may be resubmitted once within two weeks of feedback. Resubmission must include
the original submission and a short note on what changed and why. The capstone has one
resubmission with the same rule.

## Feedback that helps

When you ask for review, include:

- the command you ran and its output,
- the split rule and how you verified it,
- the metric, its sample size, and its threshold,
- one thing you are unsure about.

"I got 0.93, is that good?" cannot be answered. "0.93 on 45 grouped test images, 100
sources, three classes, no per-class breakdown - is the class balance a problem?" can.
