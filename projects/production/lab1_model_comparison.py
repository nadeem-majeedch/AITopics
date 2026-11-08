"""Lab 1 - compare two models on the same held-out test set.

What the lab fixes before it measures anything:

* **The split.** 60/20/20, stratified, one seed. Both models see the same rows.
* **The selection rule.** The operating threshold and the model choice are made
  on validation data. Test data is scored once, after the decision.
* **The comparison.** Paired bootstrap over rows, because both models scored the
  same rows and unpaired intervals would inflate the difference.

The dataset is synthetic and imbalanced (about 30% churn), so accuracy alone is
misleading. The lab reports accuracy next to macro-F1, precision/recall, and AUC,
and the conclusion is allowed to be "the simpler model is as good".

    python lab1_model_comparison.py
    python lab1_model_comparison.py --selftest
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_core import (  # noqa: E402
    Checks,
    Report,
    base_parser,
    bootstrap_ci,
    data,
    duplicate_overlap,
    environment_snapshot,
    expected_calibration_error,
    fmt,
    leak_audit,
    macro_f1,
    measured_footer,
    metrics,
    paired_bootstrap_diff,
    precision_recall_f1,
    random_split,
    stratified_split,
    write_json,
)

OUT_DIR = data.ROOT / "outputs" / "production" / "lab1"
SEED = 7
NUMERIC = ["tenure_months", "monthly_charges", "support_tickets", "usage_gb"]
CATEGORICAL = ["contract_type", "region"]
FEATURES = NUMERIC + CATEGORICAL


def load_split():
    data.ensure_data()
    rows = data.load_csv(data.DATA / "customers" / "customers.csv")
    train, val, test = stratified_split(rows, "churned", (0.6, 0.2, 0.2), seed=SEED)
    return rows, train, val, test


def fit_models(train: list[dict], val: list[dict]):
    x_train, names, levels = data.feature_matrix(train, NUMERIC, CATEGORICAL)
    x_val, _, _ = data.feature_matrix(val, NUMERIC, CATEGORICAL, levels)
    y_train = np.array(data.target(train))
    y_val = np.array(data.target(val))

    models = {
        "logistic_regression": LogisticRegression(max_iter=2000, random_state=SEED),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.08, max_leaf_nodes=15, random_state=SEED
        ),
    }
    probabilities = {}
    for name, model in models.items():
        model.fit(x_train, y_train)
        probabilities[name] = model.predict_proba(x_val)[:, 1]
    return models, names, levels, probabilities, y_val


def choose_threshold(y_true: np.ndarray, probs: np.ndarray) -> float:
    """Pick the F1-maximising threshold on validation data only."""
    best = (0.5, -1.0)
    for threshold in np.linspace(0.05, 0.95, 91):
        f1 = precision_recall_f1(y_true, (probs >= threshold).astype(int))["f1"]
        if f1 > best[1]:
            best = (float(threshold), f1)
    return best[0]


def score(y_true: np.ndarray, probs: np.ndarray, threshold: float) -> dict:
    preds = (probs >= threshold).astype(int)
    prf = precision_recall_f1(y_true, preds)
    return {
        "accuracy": metrics.accuracy(y_true, preds),
        "macro_f1": macro_f1(y_true, preds),
        "precision": prf["precision"],
        "recall": prf["recall"],
        "f1": prf["f1"],
        "auc": metrics.roc_auc(y_true, probs),
        "average_precision": metrics.average_precision(y_true, probs),
        "log_loss": metrics.log_loss(y_true, probs),
        "ece": expected_calibration_error(y_true, probs),
        "base_rate": float(np.mean(y_true)),
        "threshold": threshold,
    }


def run(seed: int = SEED) -> dict:
    rows, train, val, test = load_split()
    models, names, levels, val_probs, y_val = fit_models(train, val)

    # Model choice and threshold are validation decisions, recorded before test.
    threshold = choose_threshold(y_val, val_probs["logistic_regression"])
    val_scores = {name: score(y_val, probs, threshold) for name, probs in val_probs.items()}
    chosen = max(val_scores, key=lambda name: (val_scores[name]["f1"], -len(name)))

    x_test, _, _ = data.feature_matrix(test, NUMERIC, CATEGORICAL, levels)
    y_test = np.array(data.target(test))
    test_probs = {name: model.predict_proba(x_test)[:, 1] for name, model in models.items()}
    test_scores = {name: score(y_test, probs, threshold) for name, probs in test_probs.items()}

    correct_a = (test_probs["logistic_regression"] >= threshold).astype(int) == y_test
    correct_b = (test_probs["hist_gradient_boosting"] >= threshold).astype(int) == y_test
    diff = paired_bootstrap_diff(correct_a.astype(float), correct_b.astype(float), seed=seed)
    accuracy_ci = {
        name: bootstrap_ci(correct.astype(float), seed=seed)
        for name, correct in (("logistic_regression", correct_a), ("hist_gradient_boosting", correct_b))
    }

    # An honest report states the split overlap it actually had.
    overlap = duplicate_overlap(train, test, FEATURES)
    random_train, _, random_test = random_split(rows, seed=seed)
    audit = leak_audit(rows, NUMERIC + ["account_status"], target_key="churned")
    audit_used = [item for item in audit if item["feature"] in NUMERIC]

    return {
        "seed": seed,
        "rows": len(rows),
        "sizes": {"train": len(train), "validation": len(val), "test": len(test)},
        "features": names,
        "chosen_model": chosen,
        "threshold": threshold,
        "validation": val_scores,
        "test": test_scores,
        "paired_accuracy_difference": diff,
        "accuracy_ci": {name: {"accuracy": ci[0], "low": ci[1], "high": ci[2]} for name, ci in accuracy_ci.items()},
        "duplicate_overlap": overlap,
        "stratified_audit": audit_used,
        "random_split_overlap": duplicate_overlap(random_train, random_test, FEATURES),
        "predictions": {
            "y_true": y_test.tolist(),
            "logistic_regression": test_probs["logistic_regression"].tolist(),
            "hist_gradient_boosting": test_probs["hist_gradient_boosting"].tolist(),
        },
        "environment": environment_snapshot(),
    }


def build_report(result: dict) -> Report:
    report = Report(
        "Lab 1 - comparing two models on one held-out test set",
        "Synthetic subscription-churn data, generated by `scripts/make_eval_data.py`.",
    )
    report.heading("Setup")
    report.bullets([
        f"Seed {result['seed']}; {result['rows']} rows split "
        f"{result['sizes']['train']}/{result['sizes']['validation']}/{result['sizes']['test']} "
        "(train/validation/test), stratified on the label.",
        "The threshold and the model were chosen on validation data. The test set was scored once.",
        f"Test base rate: {result['test']['logistic_regression']['base_rate']:.3f}.",
    ])

    report.heading("Validation results (used for the decision)")
    report.table(
        [{"model": name, **scores} for name, scores in result["validation"].items()],
        ["model", "accuracy", "macro_f1", "f1", "auc", "log_loss", "threshold"],
    )

    report.heading("Test results (reported once)")
    report.table(
        [{"model": name, **scores} for name, scores in result["test"].items()],
        ["model", "accuracy", "macro_f1", "precision", "recall", "f1", "auc", "average_precision", "ece"],
    )

    diff = result["paired_accuracy_difference"]
    report.heading("Is the difference real?")
    report.text(
        f"Paired bootstrap of accuracy (logistic regression minus gradient boosting): "
        f"{diff['difference']:+.3f}, 95% interval [{diff['low']:+.3f}, {diff['high']:+.3f}]. "
        + ("The interval includes zero, so this test set does not establish a difference."
           if diff["includes_zero"] else
           "The interval excludes zero, but the effect is small; check slices and cost before switching.")
    )
    report.table(
        [{"model": name, **ci} for name, ci in result["accuracy_ci"].items()],
        ["model", "accuracy", "low", "high"],
    )

    report.heading("Leakage checks")
    report.bullets([
        f"Duplicate-row overlap between train and test: {result['duplicate_overlap']['matched']} of "
        f"{result['duplicate_overlap']['test_rows']} test rows "
        f"({result['duplicate_overlap']['fraction']:.1%}) share a feature vector with a train row.",
        "Single-feature audit for the features actually used:",
        *[f"`{item['feature']}`: {item['detail']}, suspicious={item['suspicious']}"
          for item in result["stratified_audit"]],
    ])

    report.heading("Conclusion")
    report.text(
        f"Selected **{result['chosen_model']}** at threshold {result['threshold']:.2f} on validation "
        f"macro-F1. On test, accuracy is {result['test'][result['chosen_model']]['accuracy']:.3f} "
        f"against a majority-class rate of {max(result['test'][result['chosen_model']]['base_rate'], 1 - result['test'][result['chosen_model']]['base_rate']):.3f}. "
        "Accuracy is the weakest summary here; AUC and the precision/recall pair carry the signal."
    )
    return report


def selftest() -> int:
    checks = Checks("lab 1 - model comparison")
    result = run()

    checks.equal("split sizes sum to the data", sum(result["sizes"].values()), result["rows"])
    checks.check("split is stratified within 2 points",
                 abs(result["test"]["logistic_regression"]["base_rate"]
                     - result["validation"]["logistic_regression"]["base_rate"]) < 0.02,
                 f"{result['test']['logistic_regression']['base_rate']} vs "
                 f"{result['validation']['logistic_regression']['base_rate']}")
    checks.check("both models scored the same rows",
                 len(result["predictions"]["logistic_regression"]) == len(result["predictions"]["y_true"])
                 == len(result["predictions"]["hist_gradient_boosting"]))
    checks.check("auc beats chance", result["test"]["logistic_regression"]["auc"] > 0.6,
                 fmt(result["test"]["logistic_regression"]["auc"]))
    checks.check("auc computed for both models",
                 all(0.5 < scores["auc"] <= 1.0 for scores in result["test"].values()))
    checks.check("paired interval computed with correct sign convention",
                 result["paired_accuracy_difference"]["low"] <= result["paired_accuracy_difference"]["high"])
    checks.check("threshold came from validation, not test",
                 0.05 <= result["threshold"] <= 0.95)
    checks.check("no used feature is flagged as leaky",
                 not any(item["suspicious"] for item in result["stratified_audit"]),
                 str([item["feature"] for item in result["stratified_audit"] if item["suspicious"]]))
    checks.check("overlap was measured, not assumed",
                 "fraction" in result["duplicate_overlap"])

    report = build_report(result)
    report_path = report.write(OUT_DIR, "report.md", measured_footer(result["environment"]))
    metrics_path = write_json(OUT_DIR, "metrics.json", result)
    checks.check("report written", report_path.exists() and report_path.stat().st_size > 1000)
    checks.check("metrics written", metrics_path.exists())
    checks.check("report carries the provenance footer", "Measured on" in report_path.read_text(encoding="utf-8"))
    return checks.report()


def main() -> int:
    parser = base_parser(__doc__ or "")
    args = parser.parse_args()
    if args.selftest:
        return selftest()

    result = run()
    report = build_report(result)
    path = report.write(OUT_DIR, "report.md", measured_footer(result["environment"]))
    write_json(OUT_DIR, "metrics.json", result)
    print(report.render(measured_footer(result["environment"])))
    print(f"\nwritten: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
