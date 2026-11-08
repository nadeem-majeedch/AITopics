"""Lab 2 - make leakage visible, then remove it.

Three leaks, three experiments, one model class so the only thing that changes is
the data:

**A. Target leak.** ``account_status`` is ``cancelled`` exactly when the customer
churned. It is a consequence of the label, recorded after the fact. Including it
turns a hard problem into a lookup.

**B. Missingness leak.** ``cancellation_reason`` is filled only for churners.
Even without its values, *whether it is empty* predicts the label.

**C. Duplicate leak.** The export contains the same customer twice. A row-wise
split puts the duplicate in test and the original in train, so the model is scored
on rows it memorised. This is the leak a careful student still misses, because the
split code is correct and the rows are not independent.

Each experiment reports train and test accuracy/AUC, the gap between them, and the
measured train/test overlap. The lesson is not "never trust a high score"; it is
"measure the overlap and the label-conditional fill rate before you trust a split".

    python lab2_data_leakage.py
    python lab2_data_leakage.py --selftest
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_core import (  # noqa: E402
    Checks,
    Report,
    base_parser,
    data,
    duplicate_overlap,
    environment_snapshot,
    leak_audit,
    measured_footer,
    metrics,
    random_split,
    stratified_split,
    write_json,
)

OUT_DIR = data.ROOT / "outputs" / "production" / "lab2"
SEED = 7
NUMERIC = ["tenure_months", "monthly_charges", "support_tickets", "usage_gb"]
CATEGORICAL = ["contract_type", "region"]
CLEAN = NUMERIC + CATEGORICAL


def fit_and_score(train, test, numeric, categorical):
    x_train, _, levels = data.feature_matrix(train, numeric, categorical)
    x_test, _, _ = data.feature_matrix(test, numeric, categorical, levels)
    y_train = np.array(data.target(train))
    y_test = np.array(data.target(test))
    model = LogisticRegression(max_iter=2000, random_state=SEED).fit(x_train, y_train)
    train_probs = model.predict_proba(x_train)[:, 1]
    test_probs = model.predict_proba(x_test)[:, 1]
    return {
        "train_accuracy": metrics.accuracy(y_train, (train_probs >= 0.5).astype(int)),
        "test_accuracy": metrics.accuracy(y_test, (test_probs >= 0.5).astype(int)),
        "train_auc": metrics.roc_auc(y_train, train_probs),
        "test_auc": metrics.roc_auc(y_test, test_probs),
        "gap": metrics.accuracy(y_train, (train_probs >= 0.5).astype(int))
        - metrics.accuracy(y_test, (test_probs >= 0.5).astype(int)),
        "features": len(levels) + len(numeric),
    }


def fit_memoriser(train, test, numeric, categorical):
    """A 1-nearest-neighbour model: the cheapest way to expose memorised rows."""
    x_train, _, levels = data.feature_matrix(train, numeric, categorical)
    x_test, _, _ = data.feature_matrix(test, numeric, categorical, levels)
    y_train = np.array(data.target(train))
    y_test = np.array(data.target(test))
    model = KNeighborsClassifier(n_neighbors=1).fit(x_train, y_train)
    return {"test_accuracy_knn": metrics.accuracy(y_test, model.predict(x_test))}


def with_duplicate_rate(rows: list[dict], rate: float, seed: int = SEED) -> list[dict]:
    """Construct a variant with ``rate`` extra duplicated rows, for experiment C."""
    rng = np.random.default_rng(seed)
    originals = [row for row in rows if not row["customer_id"].endswith("-DUP")]
    count = int(len(originals) * rate)
    chosen = rng.choice(len(originals), size=count, replace=False)
    duplicates = [{**originals[i], "customer_id": originals[i]["customer_id"] + "-DUP"} for i in chosen]
    return list(rows) + duplicates


def run() -> dict:
    data.ensure_data()
    rows = data.load_csv(data.DATA / "customers" / "customers.csv")
    rows = [row for row in rows if not row["customer_id"].endswith("-DUP")]  # start clean

    train, _, test = stratified_split(rows, "churned", (0.7, 0.15, 0.15), seed=SEED)
    clean = fit_and_score(train, test, NUMERIC, CATEGORICAL)
    clean_overlap = duplicate_overlap(train, test, CLEAN)

    # A. target leak: a column that is the label written differently.
    target_leak = fit_and_score(train, test, NUMERIC, CATEGORICAL + ["account_status"])

    # B. missingness leak: presence of a field that only churners have.
    for split in (train, test):
        for row in split:
            row["has_reason"] = 1 if str(row["cancellation_reason"]).strip() else 0
    missingness_leak = fit_and_score(train, test, NUMERIC + ["has_reason"], CATEGORICAL)
    fill = {
        label: sum(1 for row in rows if row["churned"] == label and str(row["cancellation_reason"]).strip())
        / max(1, sum(1 for row in rows if row["churned"] == label))
        for label in (0, 1)
    }

    # C. duplicates: same rows, two split strategies.
    duplicated = with_duplicate_rate(rows, 0.30)
    dup_train, _, dup_test = random_split(duplicated, (0.7, 0.15, 0.15), seed=SEED)
    duplicate_leak = fit_and_score(dup_train, dup_test, NUMERIC, CATEGORICAL)
    duplicate_knn = fit_memoriser(dup_train, dup_test, NUMERIC, CATEGORICAL)
    duplicate_overlap_random = duplicate_overlap(dup_train, dup_test, CLEAN)

    # Group split: keep every copy of a customer on one side.
    groups: dict[str, list[dict]] = {}
    for row in duplicated:
        key = row["customer_id"].replace("-DUP", "")
        groups.setdefault(key, []).append(row)
    rng = np.random.default_rng(SEED)
    keys = sorted(groups)
    rng.shuffle(keys)
    n_train = int(len(keys) * 0.7)
    n_val = int(len(keys) * 0.15)
    group_train = [row for key in keys[:n_train] for row in groups[key]]
    group_test = [row for key in keys[n_train + n_val :] for row in groups[key]]
    grouped = fit_and_score(group_train, group_test, NUMERIC, CATEGORICAL)
    grouped_knn = fit_memoriser(group_train, group_test, NUMERIC, CATEGORICAL)
    grouped_overlap = duplicate_overlap(group_train, group_test, CLEAN)

    audit = leak_audit(rows, NUMERIC + ["account_status", "cancellation_reason"])
    return {
        "seed": SEED,
        "rows": len(rows),
        "sizes": {"train": len(train), "test": len(test)},
        "clean": clean,
        "target_leak": target_leak,
        "missingness_leak": missingness_leak,
        "fill_rate_by_label": fill,
        "duplicate_rate": 0.30,
        "duplicate_random_split": {**duplicate_leak, **duplicate_knn, "overlap": duplicate_overlap_random},
        "duplicate_group_split": {**grouped, **grouped_knn, "overlap": grouped_overlap},
        "audit": audit,
        "environment": environment_snapshot(),
    }


def build_report(result: dict) -> Report:
    report = Report(
        "Lab 2 - how leakage inflates an evaluation",
        "The same logistic regression, four feature sets. Only the data changes.",
    )
    report.heading("What was measured")
    report.bullets([
        f"{result['rows']} independent rows; train {result['sizes']['train']}, test {result['sizes']['test']}.",
        "Accuracy and AUC are reported on train and test, with the gap between them.",
        f"Duplicate experiment: {result['duplicate_rate']:.0%} of rows duplicated before splitting.",
    ])

    report.heading("Experiments")
    rows = [
        {"experiment": "clean features", "model": "logistic", **result["clean"]},
        {"experiment": "+ account_status (target leak)", "model": "logistic", **result["target_leak"]},
        {"experiment": "+ has_reason (missingness leak)", "model": "logistic", **result["missingness_leak"]},
    ]
    report.table(rows, ["experiment", "model", "train_accuracy", "test_accuracy", "train_auc", "test_auc", "gap"])

    duplicate_rows = [
        {"split": "random (leaky)", "model": "logistic regression",
         "test_accuracy": result["duplicate_random_split"]["test_accuracy"],
         "overlap": result["duplicate_random_split"]["overlap"]["fraction"]},
        {"split": "grouped by customer", "model": "logistic regression",
         "test_accuracy": result["duplicate_group_split"]["test_accuracy"],
         "overlap": result["duplicate_group_split"]["overlap"]["fraction"]},
        {"split": "random (leaky)", "model": "1-nearest-neighbour",
         "test_accuracy": result["duplicate_random_split"]["test_accuracy_knn"],
         "overlap": result["duplicate_random_split"]["overlap"]["fraction"]},
        {"split": "grouped by customer", "model": "1-nearest-neighbour",
         "test_accuracy": result["duplicate_group_split"]["test_accuracy_knn"],
         "overlap": result["duplicate_group_split"]["overlap"]["fraction"]},
    ]
    report.table(duplicate_rows, ["split", "model", "test_accuracy", "overlap"])

    report.heading("Why each number moved")
    report.text(
        f"`account_status` is `cancelled` exactly when `churned == 1`, so test accuracy rises to "
        f"{result['target_leak']['test_accuracy']:.3f}. The model learned the export format, not the customer.\n\n"
        f"`cancellation_reason` is filled for {result['fill_rate_by_label'][1]:.0%} of churners and "
        f"{result['fill_rate_by_label'][0]:.0%} of non-churners. The *presence* of that field alone lifts "
        f"test accuracy to {result['missingness_leak']['test_accuracy']:.3f}.\n\n"
        f"With {result['duplicate_rate']:.0%} duplicates, {result['duplicate_random_split']['overlap']['fraction']:.1%} "
        f"of test rows share a feature vector with a training row. Logistic regression reads "
        f"{result['duplicate_random_split']['test_accuracy']:.3f} on the random split and "
        f"{result['duplicate_group_split']['test_accuracy']:.3f} grouped: it draws a smooth boundary, so a "
        f"memorised row does not help it much. A 1-nearest-neighbour model reads "
        f"{result['duplicate_random_split']['test_accuracy_knn']:.3f} versus "
        f"{result['duplicate_group_split']['test_accuracy_knn']:.3f}. The leak is the same; the damage depends "
        f"on how much the model can memorise. Group by entity, not by row."
    )

    report.heading("What the audit found")
    report.table(
        [{"feature": item["feature"], "score": item["score"], "fill_gap": item["fill_gap"],
          "suspicious": item["suspicious"], "reason": item["reason"]}
         for item in result["audit"]],
        ["feature", "score", "fill_gap", "suspicious", "reason"],
    )
    return report


def selftest() -> int:
    checks = Checks("lab 2 - data leakage")
    result = run()

    clean, target, missing = result["clean"], result["target_leak"], result["missingness_leak"]
    checks.check("clean test AUC is realistic, not perfect", 0.6 < clean["test_auc"] < 0.85,
                 f"{clean['test_auc']:.3f}")
    checks.check("target leak raises test accuracy by at least 0.15",
                 target["test_accuracy"] - clean["test_accuracy"] >= 0.15,
                 f"{clean['test_accuracy']:.3f} -> {target['test_accuracy']:.3f}")
    checks.check("target leak drives AUC close to 1", target["test_auc"] > 0.97,
                 f"{target['test_auc']:.3f}")
    checks.check("missingness leak raises accuracy",
                 missing["test_accuracy"] > clean["test_accuracy"],
                 f"{clean['test_accuracy']:.3f} -> {missing['test_accuracy']:.3f}")
    checks.check("fill rate differs sharply between labels",
                 abs(result["fill_rate_by_label"][1] - result["fill_rate_by_label"][0]) > 0.4,
                 str({k: round(v, 3) for k, v in result["fill_rate_by_label"].items()}))

    dup_random = result["duplicate_random_split"]
    dup_grouped = result["duplicate_group_split"]
    checks.check("random split leaks duplicates into test", dup_random["overlap"]["fraction"] > 0.15,
                 f"{dup_random['overlap']['fraction']:.3f}")
    checks.equal("grouped split has zero overlap", dup_grouped["overlap"]["fraction"], 0.0)
    inflation = dup_random["test_accuracy_knn"] - dup_grouped["test_accuracy_knn"]
    checks.check("duplicates inflate a memorising model by at least 10 points", inflation >= 0.10,
                 f"{dup_random['test_accuracy_knn']:.3f} vs {dup_grouped['test_accuracy_knn']:.3f}")
    checks.check("a smooth model is barely moved by the same duplicates",
                 abs(dup_random["test_accuracy"] - dup_grouped["test_accuracy"]) < 0.05,
                 f"{dup_random['test_accuracy']:.3f} vs {dup_grouped['test_accuracy']:.3f}")

    flagged = {item["feature"] for item in result["audit"] if item["suspicious"]}
    checks.check("audit flags the target leak", "account_status" in flagged, str(flagged))
    checks.check("audit flags the missingness leak", "cancellation_reason" in flagged, str(flagged))
    checks.check("audit leaves honest features alone",
                 not flagged & {"tenure_months", "monthly_charges", "support_tickets", "usage_gb"},
                 str(flagged))

    report = build_report(result)
    path = report.write(OUT_DIR, "report.md", measured_footer(result["environment"]))
    write_json(OUT_DIR, "metrics.json", result)
    checks.check("report written", path.exists() and path.stat().st_size > 800)
    return checks.report()


def main() -> int:
    parser = base_parser(__doc__ or "")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    result = run()
    print(build_report(result).render(measured_footer(result["environment"])))
    write_json(OUT_DIR, "metrics.json", result)
    print(f"\nwritten: {OUT_DIR / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
