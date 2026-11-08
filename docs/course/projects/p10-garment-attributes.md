# P10 - Clothing category and garment colour recognition

```markdown
**Projects:** [Index](index.md) · [Completion checklist](completion-checklist.md) · [Report template](report-template.md)
```

| | |
| --- | --- |
| **Difficulty** | Intermediate |
| **Effort** | 40-55 hours |
| **Hardware** | CPU is enough for the synthetic garment set; a GPU helps with real photographs |
| **Prerequisites** | [CV03 preprocessing](../../lessons/computer-vision/cv03-preprocessing-and-augmentation.md), [CV06 transfer learning](../../lessons/computer-vision/cv06-transfer-learning.md), [CV07 fine-tuning](../../lessons/computer-vision/cv07-fine-tuning.md), [CV12 embeddings](../../lessons/computer-vision/cv12-embeddings-and-similarity.md), [VD10 clothing and appearance](../../lessons/video-ai/vd10-clothing-and-appearance.md), [VD15 responsible analytics](../../lessons/video-ai/vd15-responsible-video-analytics.md) |
| **Builds on** | Video AI lab 5 and the Computer Vision transfer-learning labs |
| **Hard limit** | Garment attributes only. No inference about the person wearing them. |

## 1. Problem statement and motivation

An online retailer with a small catalogue needs every product photo tagged with a
garment category (shirt, trousers, dress, jacket, shoe) and a dominant colour, so
that search and filtering work. Manual tagging is slow and inconsistent: two people
disagree about whether a colour is "olive" or "khaki".

The task has two heads with different failure modes. Category errors are usually
about shape and silhouette; colour errors are about lighting, white balance, and
background. Treating them as one problem hides both.

**Decision supported:** a suggested tag set for a catalogue item, with confidence,
for a human to accept or correct. Never a decision about a person.

## 2. Intended learning outcomes

1. Build a two-head model (category and colour) or two models, and justify the choice.
2. Define a colour taxonomy with measured agreement between annotators.
3. Evaluate each head separately with macro F1 and a confusion matrix.
4. Show that colour predictions are sensitive to lighting and white balance, and
   quantify it.
5. Use a segmentation or background mask to test whether the model reads the
   garment or the scene.
6. Calibrate confidence and abstain on uncertain items.
7. State clearly why person-level attribute inference is out of scope and harmful.

## 3. Difficulty and prerequisites

**Level:** Intermediate. 40-55 hours: 10 data and taxonomy, 10 modelling, 14
evaluation, 8 robustness, 8 packaging and writing.

Requires CV06/CV07 and VD10. You should be comfortable with a multi-output model or
with running two independent classifiers.

## 4. Scope and out-of-scope features

**In scope**

- 4-8 garment categories and 8-12 named colours.
- Single-label category and single-label dominant colour per item.
- Two-head model or two models, compared fairly.
- Robustness tests: brightness, white balance shift, background substitution,
  occlusion by a bag or hand.
- A CLI that tags one image or a folder and writes a CSV.

**Out of scope**

- Person identification, body measurements, size estimation, or "is this
  appropriate to wear" judgements.
- Attribute inference about the wearer (age, gender, profession, income).
- Fine-grained fashion attributes (sleeve type, neckline) unless you add them as a
  documented extension with their own evaluation.
- Video try-on or generation.
- Scraped catalogue images without a licence.

## 5. Dataset options, licences, and preparation

| Option | Source | Licence | Notes |
| --- | --- | --- | --- |
| A (default, offline) | Synthetic garments from `video_core.garments` (used by `projects/video-ai/lab5_garment_attributes.py`) | CC0-1.0, generated | Controllable colour and category, exact labels, fast on CPU |
| B | Fashionpedia or DeepFashion | Each has its own terms; DeepFashion is commonly research-only | Record the exact licence and whether derivative models may be published |
| C | Your own catalogue photos | Yours | Best for realism; 40+ per category, varied lighting |
| D | Fashion-MNIST | MIT per the repository | Category only, 28x28 greyscale - no colour head |

**Preparation (option A)**

1. Generate or load the synthetic garment set using `video_core.garments`. Run
   `python projects/video-ai/lab5_garment_attributes.py --selftest` once to see the
   module and its two report functions in action, then export images and labels to
   disk with your own script so the dataset is reproducible outside a notebook.
2. Write the colour taxonomy as a table: name, hex reference, acceptable variants,
   and the nearest neighbour it is often confused with (olive/khaki, navy/black).
3. Label 30 items twice, a day apart, and report agreement per head. If colour
   agreement is below 80%, simplify the taxonomy before modelling.
4. Split by garment instance, not by augmentation. Record counts per class per split.
5. For real photos, capture the lighting conditions and note them per image; you
   will need them for the robustness analysis.

## 6. Recommended baseline

**Colour histogram plus nearest reference colour** for the colour head, and a small
CNN or logistic regression on downscaled pixels for the category head. Both are
cheap and expose whether the task is trivial.

Second baseline: a single multi-class model over the combined category-colour label
space (for example 5 categories x 10 colours). Compare it with two heads; the
combined model often wins on frequent pairs and loses on rare ones, and reporting
that is more useful than picking one silently.

## 7. Milestones

| # | Milestone | Evidence | Hours |
| --- | --- | --- | --- |
| 1 | Taxonomy and labels | Colour table, agreement scores, split audit | 10 |
| 2 | Baselines | Histogram colour model, small category model | 8 |
| 3 | Two-head model | Training, per-head metrics | 12 |
| 4 | Robustness | Lighting, white balance, background, occlusion | 10 |
| 5 | Calibration and abstention | Reliability table per head, threshold | 6 |
| 6 | Package | CLI, model card, report | 9 |

## 8. Repository or folder structure

```text
capstone-p10/
  README.md
  requirements.txt
  configs/
    train.yaml
    colours.json          # taxonomy: name, hex, variants
  data/
    dataset-card.md
    label-guide.md
    splits.json
  src/
    export_data.py        # synthetic set or catalogue photos -> images + labels
    colour.py             # reference colours, histogram baseline, delta-E
    model.py              # two heads, shared or separate backbones
    train.py
    evaluate.py           # per-head metrics, confusion, calibration
    robustness.py         # brightness, white balance, background, occlusion
    predict.py            # image or folder -> csv
  tests/
    test_colour.py
    test_splits.py
    test_predict.py
  reports/
    report.md
    model-card.md
  outputs/
    metrics.json
    predictions.csv
```

## 9. Detailed development tasks

1. `export_data.py`: write images, labels, and a manifest. Deterministic at a fixed
   seed if synthetic. Verify pixel ranges and image sizes.
2. `colour.py`: implement nearest reference colour in a perceptually reasonable
   space (Lab or HSV with care) and a histogram baseline. Report accuracy of the
   baseline alone before any learning.
3. `model.py`: shared backbone with two heads, or two independent models. Document
   the loss weighting if shared. Justify your choice in one paragraph.
4. Train with category and colour losses logged separately. A combined loss that
   falls while one head is broken is a common trap.
5. Evaluate per head: macro F1, per-class precision/recall, confusion matrix, and
   top-2 accuracy for colour. Report category-colour joint accuracy as a secondary
   number, not the headline.
6. Calibration per head: reliability table and ECE; temperature scaling on
   validation if needed. Report before and after.
7. `robustness.py`: brightness ±30%, warm and cool white balance shifts, background
   replacement with a neutral grey, and a rectangular occlusion over 20% of the
   garment. Report each head's macro F1 under each perturbation.
8. Background test: train a category model on images with the background masked to
   grey and compare. If accuracy barely changes, the model was reading the garment;
   if it collapses, it was reading the scene. Either result is informative.
9. Abstention: threshold per head on validation. Report coverage and accuracy on the
   covered subset, and choose a threshold from a catalogue-review budget.
10. `predict.py`: one image or a folder, output CSV with category, colour, both
    confidences, and an `needs_review` flag.
11. Model card: classes, colour taxonomy limits, lighting sensitivity, prohibited
    uses (no person attributes, no size estimation, no moderation decisions).
12. Latency and model size on CPU.

## 10. Testing and evaluation plan

| Test | Proves | Pass condition |
| --- | --- | --- |
| Colour conversion test | Reference matching is correct | Known RGB values map to the expected names |
| Split test | No instance crosses splits | Intersection empty |
| Head isolation test | Each head can be evaluated alone | Disabling one head leaves the other's predictions unchanged |
| Calibration test | Bins are right | Toy array matches expected ECE |
| Background test | Shortcut is measured | Masked-background result reported |
| CLI test | Works outside notebook | Folder mode writes one row per image |

Protocol: tune on validation, test once. Robustness and background experiments are
reported separately and never used to select the model.

## 11. Metrics

**Quantitative**

| Metric | Why |
| --- | --- |
| Category macro F1 | Balance across garment types |
| Colour macro F1 and top-2 accuracy | Near-colours are the real ambiguity |
| Joint accuracy | Catalogue usefulness, reported secondarily |
| Per-head ECE | Confidence is shown to reviewers |
| Macro F1 under each perturbation | Honest robustness |
| Coverage at the review threshold | Reviewer workload |
| Latency and size | Catalogue batch processing |

**Qualitative**

- Confusion pairs that are taxonomy problems rather than model problems.
- Whether lighting changes hue in a way a human would also get wrong.
- A statement that synthetic garments are not photographs and that the numbers do
  not transfer without evaluation on real images.

## 12. Expected deliverables

- [ ] Colour taxonomy with agreement scores.
- [ ] Dataset card, label guide, split audit.
- [ ] Baseline and two-head results, per head.
- [ ] Confusion matrices and calibration tables per head.
- [ ] Robustness table with four perturbations.
- [ ] Background-mask control experiment.
- [ ] CLI with review flag.
- [ ] Model card and report.
- [ ] Tests passing.

## 13. Suggested extensions

- Add multi-label colour (a striped shirt has two colours) with a documented rule.
- Add a retrieval mode: given a garment, find the five most similar catalogue items.
- Compare Lab and HSV colour spaces for the baseline and report the difference.
- Add a "colour name disagreement" metric using two annotators on 50 items.

## 14. Common failure modes and troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Colour accuracy high on synthetic, poor on photos | White balance differences | Report the gap; add white-balance normalisation and re-measure |
| Category model reads the background | Scene correlates with class in your data | Background-mask control; augment backgrounds |
| One head dominates training | Loss weighting | Log losses separately; balance weights |
| Olive and khaki always confused | Taxonomy overlap | Merge, or report as an accepted confusion |
| Confidence high on wrong colour | Uncalibrated head | Temperature scaling; abstain |
| Dataset labels disagree between annotators | Ambiguous taxonomy | Simplify; report agreement before modelling |
| Model predicts colour of a nearby object | No garment localisation | Add a mask or crop step; evaluate with and without |

## 15. Marking rubric

| Criterion | Weight | 4 - Excellent | 3 - Meets | 2 - Approaching | 1 - Not yet |
| --- | --- | --- | --- | --- | --- |
| Taxonomy and data quality | 20% | Agreement measured, splits audited, provenance clear | Clean labels and splits | Ambiguous labels | Unlicensed or leaking data |
| Model design | 20% | Two-head justification, separated losses, fair baselines | Working model with baselines | One model, no baseline | Unexplained |
| Per-head evaluation | 25% | Confusion, calibration, joint and per-head metrics | Correct per-head metrics | Combined metric only | No evaluation |
| Robustness and shortcut testing | 20% | Four perturbations plus background control | Basic robustness | Mentioned only | Ignored |
| Reproducibility and communication | 15% | Config, CLI, model card, precise limits | Runs and documents | Thin | Cannot rerun |

**Bands:** 90-100 portfolio-ready; 80-89 solid; 70-79 works, analysis thin; below
70 the per-head claim is unsupported.

## 16. Self-review checklist

- [ ] Colour taxonomy is written down with examples and agreement scores.
- [ ] Splits are by garment instance.
- [ ] Category and colour metrics are reported separately.
- [ ] Calibration is measured per head.
- [ ] At least four perturbations are measured.
- [ ] The background control experiment is reported.
- [ ] Abstention threshold comes from a review budget.
- [ ] Model card forbids person-attribute inference.
- [ ] No catalogue images are committed without a licence.

## 17. Report template

Use the shared [report template](report-template.md), adding:

1. **Taxonomy** - categories, colours, agreement, boundary decisions.
2. **Two heads** - architecture choice and loss handling.
3. **Results per head** - confusion, calibration, joint accuracy.
4. **Robustness** - perturb-and-measure table and the background control.

## 18. Demonstration and presentation checklist

- [ ] Tag five images: four clear, one ambiguous colour.
- [ ] Show per-head confusion matrices.
- [ ] Show a lighting perturbation and the change in colour prediction.
- [ ] Show the background-mask result.
- [ ] Show the review flag on an uncertain item.
- [ ] State the person-attribute prohibition and why.
- [ ] Answer: "How would you onboard a new colour name?"

**Demo trap:** showing only clean studio images. Bring the warm-white-balance one.

---

**Previous:** [P09 video analytics](p09-video-vehicle-analytics.md) · **Next:** [P11 action recognition](p11-action-recognition.md) · [Index](index.md)
