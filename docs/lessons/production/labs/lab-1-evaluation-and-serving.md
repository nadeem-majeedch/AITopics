# Lab 1 - Evaluation report and a served endpoint {#lab-1}

**Section:** [Evaluation and production](../index.md) · **Module:** M16 · **Time:** 10 hours

## Goal

Produce an evaluation a reviewer can audit and a loopback endpoint that serves the
evaluated artifact, with a card, a manifest, and a rollback plan.

## Steps

1. Train or load a classifier on a dataset you can describe. Use a 60/20/20 split;
   keep the test split untouched until the final evaluation.
2. Report accuracy with a Wilson interval, ROC AUC, precision/recall/F1 at a stated
   threshold, and the confusion matrix. Include n.
3. Build a reliability table with 5 bins and report ECE and Brier. Fit temperature
   on validation and compare on test with a paired bootstrap. Keep whichever is
   better and say why.
4. Compare the training data with two live windows (or two time slices of your
   data). Report PSI per feature and a hold/investigate decision.
5. Evaluate an input guard on at least 10 attacks and 10 benign requests. Report
   recall, false-positive rate, and the misses.
6. Render a model card and run section validation and claims audit. Fix any
   unsupported number by removing the claim or adding a measured metric.
7. Write the model, card, and manifest. Verify the manifest; then tamper with a
   copy and show the failure.
8. Serve the model on `127.0.0.1` with a JSON endpoint. Send at least 30 requests
   and report p50, p95, max, status codes, and one sample response.
9. Write a rollback plan: previous artifact digest, trigger, and procedure.

## Deliverables

| File | Contents |
| --- | --- |
| `report.md` | Metrics, intervals, calibration decision, drift decision, guard table |
| `model_card.md` | Generated card |
| `manifest.json` | Digests for model, card, tokenizer/preprocessing |
| `server.py` | Loopback endpoint |
| `latency.csv` | One row per request: ms, status |
| `rollback.md` | Previous digest, trigger, steps |

## Marking

* **25%** metrics have intervals, n, and a stated threshold.
* **15%** calibration has a decision, including a negative result if that is what
  you measured.
* **15%** drift report names features and a next action.
* **15%** guard reports both recall and FPR and analyzes misses.
* **15%** card passes validation and audit; manifest verifies and tamper test fails.
* **15%** latency reports p50/p95 and the endpoint's missing production controls.

## Rules

No deployment to a public host is required. Do not fit calibration or choose the
threshold on test. Do not hand-edit the card; regenerate it from measurements.
