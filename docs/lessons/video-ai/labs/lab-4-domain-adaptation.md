# Lab 4 - Adapt a pretrained detector to the vehicle domain

**Section path:** [Overview](../index.md) · Modules [VD09](../vd09-vehicle-classification-and-adaptation.md), [VD13](../vd13-fine-tuning.md) · **Lab 4** · [Assessment](../assessment.md)

| | |
| --- | --- |
| **Weight** | 14% of the section assessment |
| **Time** | 4 hours |
| **Hardware** | CPU-only; ~1 min the first run (fine-tuning), ~10 s after (cached weights) |
| **Code** | `projects/video-ai/lab4_domain_adaptation.py` |
| **Prerequisites** | [Lab 2](lab-2-object-detection.md), [Lab 3](lab-3-tracking-and-counting.md), VD09, VD13 |

## Objectives

1. Fine-tune a COCO detector on four vehicle classes and state exactly what was transferred.
2. Choose an operating threshold on the **validation** clip, with the curve shown.
3. Compare three models - zero-shot, fine-tuned, from-scratch - on four videos none of them
   trained on.
4. State, in your own report, that this is **frame-level (image-model) fine-tuning** and that no
   temporal model was trained.

!!! warning "The distinction this lab is built around"
    A detector that runs inference on video is not a video model. A fine-tuned detector is not a
    fine-tuned video model. Nothing in this lab passes a clip to a network. [Lab 6](lab-6-action-recognition.md)
    is where a genuinely temporal model is trained, and [VD13](../vd13-fine-tuning.md) explains
    what a true temporal fine-tune would require.

## Prerequisites

- Lab 2 (the baseline detector and its failure numbers) and Lab 3 (why a better detector is
  worth the effort for counting).
- Cached weights for the fine-tune: `outputs/cache/ssdlite_traffic_e5_s2_lr0.0003_seed0.pt`. The
  lab trains and writes it on first run.
- COCO SSDLite weights cached in `projects/video-ai/.cache/torch`.

## Procedure

### 1. Run it

```bash
cd projects/video-ai
python lab4_domain_adaptation.py
```

| Flag | Meaning |
| --- | --- |
| `--epochs 8` | longer fine-tune (different cache key, so it trains) |
| `--score-threshold 0.5` | pin the fine-tuned model's threshold instead of choosing on val |
| `--limit 20` | fewer frames per video (faster, noisier) |
| `--selftest` | 20 frames per video, checks only |

### 2. Read the transfer line

```
baseline   : ssdlite320_mobilenet_v3_large, COCO 2017, 3,440,060 parameters, untouched
fine-tuned : loaded from cache (ssdlite_traffic_e5_s2_lr0.0003_seed0)
scope      : frame-level fine-tuning. No clip, no temporal layer, no video model was trained
scratch    : TinyDetector, 138,579 parameters, trained on this section's frames only
```

And at the end, `404 tensors` copied from COCO into the new model. That number is the evidence
that "fine-tuned" is not decorative: the backbone and regression path survived, the 4-class heads
did not.

### 3. Read the threshold table before the results

| Threshold | mAP@0.5 | precision | recall | F1 |
| --- | --- | --- | --- | --- |
| 0.30 | 0.224 | 0.019 | 0.688 | 0.037 |
| 0.40 | 0.216 | 0.069 | 0.500 | 0.122 |
| 0.50 | 0.211 | 0.273 | 0.450 | 0.340 |
| **0.60** | 0.156 | 0.670 | 0.312 | **0.426** |
| 0.70 | 0.030 | 0.765 | 0.054 | 0.101 |

0.6 won on F1 and is applied, unchanged, to all four test videos. Answer this before you look at
the results: *why is mAP highest at 0.3 while F1 peaks at 0.6?*

### 4. Compare the columns

| Video | zero-shot | fine-tuned | scratch | recall (fine-tuned) |
| --- | --- | --- | --- | --- |
| `street_quiet` (val) | 0.000 | 0.156 | 0.289 | 0.312 |
| `street_night` | 0.000 | 0.033 | 0.096 | 0.044 |
| `street_rain` | 0.000 | 0.033 | 0.297 | 0.022 |
| `street_shake` | 0.100 | 0.295 | 0.443 | 0.303 |

Three claims you must be able to defend, all true at once:

- fine-tuning improved mAP on **4 of 4** held-out videos;
- it did **not** reach the in-domain from-scratch detector (0.156 vs 0.289);
- zero-shot was at 0.000 on three of four, which is why "just use a pretrained model" fails here.

### 5. Look at the annotated frames

```
outputs/lab4_<model>_<video>.png
```

One frame per model per video. Find a frame where the fine-tuned model finds a vehicle the
zero-shot one misses, and one where it produces a duplicate box. Both exist.

## Expected output

```
=== before and after
  video         coco_zo  finetuned  scratch  delta_finetuned  coco_recall  finetuned_recall
  street_quiet  0.000    0.156      0.289    0.156            0.000        0.312
  street_night  0.000    0.033      0.096    0.033            0.000        0.044
  street_rain   0.000    0.033      0.297    0.033            0.000        0.022
  street_shake  0.100    0.295      0.443    0.195            0.100        0.303
  fine-tuning improved mAP on 4 of 4 held-out videos

  [PASS] fine-tuning improved at least one held-out video  (4 improved)
  [PASS] the fine-tuned model finds vehicles at all  (recall 0.312)
  [PASS] some COCO weights were reused (this is fine-tuning)  (404 tensors)
  [PASS] the from-scratch detector is still the in-domain winner  (0.289 vs 0.156)
  [PASS] no temporal model is claimed here  (frame-level fine-tuning only; see Lab 6 ...)

  9/9 checks passed
```

## Evaluation

| Criterion | Marks | Evidence |
| --- | --- | --- |
| Three models, four held-out videos | 3 | the comparison table |
| Threshold chosen on validation, curve shown | 3 | 0.3-0.7 table + "chosen on `street_quiet`" |
| Transfer count reported and explained | 2 | 404 tensors |
| Both conclusions stated | 3 | improved 4/4 **and** lost to in-domain |
| Explicit scope statement | 2 | frame-level, no temporal layer |
| Failure analysis from the PNGs | 1 | one miss, one duplicate |

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Fine-tune takes minutes | CPU plus cold cache | expected ~41 s; check nothing else is using the CPU |
| `state_dict` size mismatch on load | cache from different `--epochs` | cache key includes epochs/lr/seed; delete stale file |
| All mAP 0.000 | class index mismatch or threshold 0.9 | check `LABEL_TO_INDEX`; print a few detections |
| Evaluated on `street_day` | in-domain, flattering | use the four test videos |
| Threshold chosen on test | invalid comparison | 0.6 comes from `street_quiet` only |
| Out of memory | two SSDLite instances alive | reuse one, or `del` before the next |

## Extensions

1. **More data.** Add `street_quiet` frames to training (and use a different validation clip -
   e.g. hold out part of `street_dusk`). Does the night column move at all?
2. **Augmentation for the shift.** Add brightness and blur augmentation and re-measure. Report
   the delta per video; expect the shake and rain columns to move first.
3. **Unfreeze more.** Train the whole network instead of the head for 5 epochs and compare. Is
   the extra capacity useful at 60 frames?
4. **Threshold per condition.** Choose a threshold per video on validation-like data and report
   what you would actually deploy. Explain why per-condition thresholds are a product decision.
5. **Honest temporal attempt.** Take the fine-tuned detector, add box smoothing across frames
   (e.g. IoU-based averaging), and measure whether counting improves. Then state whether that
   makes the model temporal (it does not - it is post-processing).

## Submit

- Full output and `outputs/lab4_domain_adaptation.json`.
- The three-way table and the threshold table.
- Your defence of the two simultaneous conclusions (improved vs zero-shot, worse than in-domain).
- One paragraph, in your own words, on why this is not a video model - and what would be needed
  for it to become one.
