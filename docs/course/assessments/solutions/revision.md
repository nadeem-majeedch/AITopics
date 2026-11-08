# Revision - answers

```markdown
**Assessments:** [Overview](../index.md) · [Solutions](index.md) · [Revision](../revision.md)
```

One point per question if the mechanism is present, half a point if correct but thin.
The answer below is the minimum; add an example if you have one.

---

## Part 1 - Data and evaluation

1. **Validation vs test:** validation is used to choose models and settings; test is used
   once for the final estimate. Using test for selection turns it into validation.
2. **Leakage without IDs:** a feature recorded after the outcome (cancellation reason), or
   preprocessing fitted on all rows before splitting (scaling, target encoding, feature
   selection).
3. **Accuracy on 3% positives:** a model that always predicts negative scores 97% and
   catches nothing; accuracy hides the class you care about. Use precision, recall, PR AUC.
4. **Bootstrap interval:** the sampling variability of a statistic if the dataset were
   redrawn from a similar population; it is not a probability that the model is correct.
5. **Calibration:** among cases predicted at probability p, about p fraction are positive.
6. **Augmentation on train only:** augmented copies are not new information, and using them
   for evaluation inflates the score and breaks the held-out assumption.
7. **Slice vs subgroup:** often used interchangeably; a slice is any defined subset of the
   evaluation data, and a subgroup usually implies a protected or decision-relevant
   population. Report counts either way.
8. **Small test set:** useful for catching gross regressions and for qualitative error
   analysis, not for precise estimates or small differences; report intervals.

## Part 2 - Modelling and training

9. **Regularisation:** trades training fit for generalisation, by penalising complexity or
   limiting capacity.
10. **Deeper tree:** can memorise noise (low bias, high variance), so training error falls
    while test error rises.
11. **Learning rate:** the step size in parameter space; too small is slow, too large
    overshoots and can diverge.
12. **Batch normalisation:** normalises activations per batch, changing gradient scale and
    allowing higher learning rates; it also adds train/eval behaviour differences.
13. **Overfitting a fine-tune:** the model reproduces training phrasing or answers instead
    of generalising; measured by held-out quality and by reproduction on training prompts.
14. **Frozen backbone:** fewer parameters to fit, so less overfitting on small data, and
    cheaper; full fine-tuning needs more data and regularisation.
15. **Learning curve:** whether more data would help (gap and slope), and how stable the
    estimate is at the current sample size.

## Part 3 - Generative and retrieval systems

16. **Retrieval:** supplies current, specific, checkable evidence the model's weights do
    not contain, and makes citations possible.
17. **Overlap:** prevents facts being cut at chunk boundaries; costs index size, duplicate
    hits, and prompt tokens.
18. **Resolving vs supporting:** resolving means the id and span exist; supporting means
    the span actually entails the claim, which needs a content check.
19. **RAG metrics beyond answer accuracy:** retrieval recall@k, MRR/nDCG, citation support
    rate, refusal rate on unanswerable questions, unsupported-claim rate.
20. **Injection via documents:** retrieved text enters the prompt, and a model can treat
    instructions in it as authoritative unless the content is delimited and treated as
    data.

## Part 4 - Vision, speech, video

21. **IoU:** intersection over union of predicted and ground-truth boxes; mAP averages AP
    over classes and IoU thresholds (mAP@0.5 uses one threshold).
22. **Instance imbalance:** per-class AP is computed from that class's detections, so a
    class with few instances has a noisy and often low AP that the mean hides.
23. **WER:** (S + D + I) / reference words after normalisation; it does not measure meaning,
    named-entity correctness, or readability.
24. **Detection-only counting:** repeated detections near the line and track loss/rebirth
    create multiple counts for one vehicle; requiring a stable id side transition fixes it.
25. **Frame vs temporal:** a frame model sees one image at a time and aggregates votes; a
    temporal model sees a sequence and can use motion, at higher cost and data needs.

## Part 5 - Production and responsibility

26. **Input vs outcome monitoring:** inputs are available immediately (distributions,
    missingness, novelty); outcomes are delayed labels or user feedback, closer to accuracy
    but late.
27. **Canary limits exposure but not proof:** the canary sample may be unrepresentative,
    the window too short, or the metric too aggregated to see a subgroup regression.
28. **Pickle risk:** deserialisation can execute arbitrary code, so an untrusted pickle is
    remote code execution; use safetensors, npz, or ONNX.
29. **Agent controls:** least-privilege tool permissions, approval for irreversible actions,
    sandboxing/path confinement, step and cost budgets, audit logging, output validation.
30. **Model card beyond README:** intended use, training data and licence, metrics with
    conditions, calibration and failure slices, prohibited uses, and known limitations.
