"""Lab 8 - decide to roll back a canary after a simulated regression.

The scenario: version 1 is serving. Version 2 was trained on a biased slice of the
data and promoted to a 20% canary. Labels arrive for the canary batch, the gate
rules are evaluated, and the registry is updated.

What the lab makes explicit:

* **The gate is written before the result is known.** Thresholds live in a policy
  dict, not in an if-statement someone edits after seeing the number.
* **Labels lag.** The trigger also uses label-free signals (input drift and the
  score distribution), because quality labels may arrive days later.
* **Rollback is a state change, not a sentence.** Traffic shares, the active
  version, and an incident record are machine-readable and reversible.
* **A gate that always fires is not a gate.** The second scenario runs a healthy
  candidate through the same rules and promotes it.

    python lab8_rollback.py
    python lab8_rollback.py --selftest
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
    data,
    drift_report,
    environment_snapshot,
    measured_footer,
    metrics,
    stratified_split,
    write_json,
)

OUT_DIR = data.ROOT / "outputs" / "production" / "lab8"
NUMERIC = ["tenure_months", "monthly_charges", "support_tickets", "usage_gb"]
CATEGORICAL = ["contract_type", "region"]
# The live export only carries the request-time fields, so drift is measured on
# the subset that exists on both sides. Comparing everything would be a bug.
DRIFT_NUMERIC = ["monthly_charges", "usage_gb", "support_tickets"]
SEED = 7

GATE = {
    "max_accuracy_drop": 0.02,
    "max_error_rate": 0.40,
    "max_psi": 0.25,
    "min_canary_rows": 150,
    "canary_share": 0.20,
}


def train(train_rows, seed: int = SEED) -> LogisticRegression:
    x, _, levels = data.feature_matrix(train_rows, NUMERIC, CATEGORICAL)
    y = np.array(data.target(train_rows))
    model = LogisticRegression(max_iter=2000, random_state=seed).fit(x, y)
    model._levels = levels  # type: ignore[attr-defined]
    return model


def train_alternative(train_rows, seed: int = SEED) -> HistGradientBoostingClassifier:
    """A different model family, for the healthy candidate."""
    x, _, levels = data.feature_matrix(train_rows, NUMERIC, CATEGORICAL)
    y = np.array(data.target(train_rows))
    model = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, random_state=seed).fit(x, y)
    model._levels = levels  # type: ignore[attr-defined]
    return model


def predict(model, rows) -> np.ndarray:
    x, _, _ = data.feature_matrix(rows, NUMERIC, CATEGORICAL, model._levels)  # type: ignore[attr-defined]
    return model.predict_proba(x)[:, 1]


def evaluate(rows, probs, threshold: float = 0.5) -> dict:
    y = np.array(data.target(rows))
    preds = (probs >= threshold).astype(int)
    return {
        "rows": len(rows),
        "accuracy": metrics.accuracy(y, preds),
        "auc": metrics.roc_auc(y, probs),
        "error_rate": 1 - metrics.accuracy(y, preds),
        "mean_score": float(np.mean(probs)),
    }


def decide(canary: dict, baseline: dict, drift: dict, policy: dict = GATE) -> dict:
    """Three outcomes, not two.

    A quality regression while the candidate serves traffic is a **rollback**.
    A healthy candidate during input drift is a **hold**: keep the canary small,
    do not widen, and investigate. Conflating the two either ships a broken model
    or throws away a good one because the input distribution moved.
    """
    quality_reasons = []
    if canary["rows"] < policy["min_canary_rows"]:
        quality_reasons.append(f"canary has only {canary['rows']} labelled rows")
    drop = baseline["accuracy"] - canary["accuracy"]
    if drop > policy["max_accuracy_drop"]:
        quality_reasons.append(f"accuracy dropped {drop:.3f} (limit {policy['max_accuracy_drop']})")
    if canary["error_rate"] > policy["max_error_rate"]:
        quality_reasons.append(f"error rate {canary['error_rate']:.3f} above {policy['max_error_rate']}")

    drift_reasons = []
    if drift["decision"] == "investigate":
        drift_reasons.append(f"input drift in {', '.join(drift['significant']) or 'unknown feature'}")

    if quality_reasons:
        action = "rollback"
    elif drift_reasons:
        action = "hold"
    else:
        action = "promote"
    return {
        "action": action,
        "rollback": action == "rollback",
        "reasons": quality_reasons + drift_reasons,
        "quality_reasons": quality_reasons,
        "drift_reasons": drift_reasons,
        "accuracy_drop": drop,
    }


def registry_update(active: str, traffic: dict[str, float], history: list[dict]) -> dict:
    return {"active_version": active, "traffic": traffic, "history": history}


def scenario(candidate: LogisticRegression, label: str, drift_week: int = 2) -> dict:
    rows = data.load_csv(data.DATA / "customers" / "customers.csv")
    train_rows, _, holdout = stratified_split(rows, "churned", (0.7, 0.15, 0.15), seed=SEED)
    baseline = train(train_rows)
    live = data.load_csv(data.DATA / "customers" / f"drift_live_w{drift_week}.csv")

    rng = np.random.default_rng(SEED)
    canary_mask = rng.random(len(holdout)) < GATE["canary_share"]
    canary_rows = [row for row, flag in zip(holdout, canary_mask) if flag]
    if len(canary_rows) < GATE["min_canary_rows"]:
        canary_rows = holdout[: GATE["min_canary_rows"]]

    baseline_probs = predict(baseline, canary_rows)
    candidate_probs = predict(candidate, canary_rows)
    baseline_metrics = evaluate(canary_rows, baseline_probs)
    candidate_metrics = evaluate(canary_rows, candidate_probs)

    drift = drift_report(train_rows, live, DRIFT_NUMERIC, ["region"])
    decision = decide(candidate_metrics, baseline_metrics, drift)

    history = [
        {"event": f"promote {label} to {GATE['canary_share']:.0%} canary", "actor": "release-bot"},
    ]
    shared = GATE["canary_share"]
    if decision["action"] == "rollback":
        history.append({"event": "rollback: 100% traffic to v1", "actor": "on-call (paged)"})
        registry = registry_update("v1", {"v1": 1.0, "v2": 0.0}, history)
    elif decision["action"] == "hold":
        history.append({"event": "hold: canary capped, no promotion", "actor": "on-call"})
        registry = registry_update("v1", {"v1": round(1 - shared, 2), "v2": shared}, history)
    else:
        history.append({"event": "promote: 100% traffic to v2", "actor": "release-bot"})
        registry = registry_update("v2", {"v1": 0.0, "v2": 1.0}, history)
    outcome = decision["action"]

    return {
        "candidate": label,
        "drift_week": drift_week,
        "canary_rows": len(canary_rows),
        "baseline": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "drift": drift,
        "decision": decision,
        "registry": registry,
        "outcome": outcome,
        "gate": GATE,
        "environment": environment_snapshot(),
    }


def build_candidates() -> tuple[LogisticRegression, LogisticRegression]:
    rows = data.load_csv(data.DATA / "customers" / "customers.csv")
    train_rows, _, _ = stratified_split(rows, "churned", (0.7, 0.15, 0.15), seed=SEED)

    # A biased candidate: trained only on monthly contracts, so it never saw the
    # segment that behaves differently. Plausible accident, not a strawman.
    monthly = [row for row in train_rows if row["contract_type"] == "monthly"]
    degraded = train(monthly, seed=SEED + 1)

    healthy = train_alternative(train_rows, seed=SEED + 2)
    return degraded, healthy


def run() -> dict:
    data.ensure_data()
    degraded, healthy = build_candidates()
    bad = scenario(degraded, "v2-trained-on-monthly-only")
    held = scenario(healthy, "v2-retrained-full-data", drift_week=2)
    good = scenario(healthy, "v2-retrained-full-data", drift_week=1)
    return {"regression": bad, "held": held, "healthy": good, "environment": environment_snapshot()}


def build_report(result: dict) -> Report:
    report = Report(
        "Lab 8 - rollback decision after a simulated regression",
        "Two candidates, one gate, two outcomes. The gate is data, not judgement in the moment.",
    )
    report.heading("Gate policy")
    report.table(
        [{"rule": key, "value": value} for key, value in result["regression"]["gate"].items()],
        ["rule", "value"],
    )
    report.text(
        "Rules are evaluated in order and any one is sufficient. The row-count rule prevents a decision on a "
        "canary too small to distinguish a real drop from noise."
    )

    for key, title in (
        ("regression", "Scenario A - biased candidate, stable week"),
        ("held", "Scenario B - healthy candidate, drifted week"),
        ("healthy", "Scenario C - healthy candidate, mild week"),
    ):
        item = result[key]
        report.heading(title)
        report.table(
            [
                {"version": "v1 (baseline)", **item["baseline"]},
                {"version": item["candidate"], **item["candidate_metrics"]},
            ],
            ["version", "rows", "accuracy", "auc", "error_rate", "mean_score"],
        )
        report.text(
            f"Accuracy drop: {item['decision']['accuracy_drop']:.3f}. Drift decision: "
            f"{item['drift']['decision']} (worst feature {item['drift']['worst']}). "
            f"Gate action: **{item['decision']['action']}**."
        )
        if item["decision"]["reasons"]:
            report.bullets([f"Gate fired: {reason}" for reason in item["decision"]["reasons"]])
        else:
            report.text("No gate fired. The candidate is promoted.")
        report.text(f"Outcome: **{item['outcome']}**. Active version: {item['registry']['active_version']}.")
        report.table(
            [{"event": entry["event"], "actor": entry["actor"]} for entry in item["registry"]["history"]],
            ["event", "actor"],
        )

    report.heading("What is still missing")
    report.bullets([
        "Labels arrive late in reality. This lab has them immediately; the drift signal is the stand-in for "
        "the period before they do.",
        "Rollback restored traffic but left the biased artifact in the registry. A real process also revokes "
        "the artifact and records why it was bad.",
        "The gate is a small set of rules. It cannot see a regression confined to a segment, which is why "
        "sliced evaluation belongs in the release checklist as well.",
    ])
    return report


def selftest() -> int:
    checks = Checks("lab 8 - rollback")
    result = run()
    bad, good = result["regression"], result["healthy"]

    checks.check("biased candidate triggers the gate", bad["decision"]["rollback"],
                 str(bad["decision"]["reasons"]))
    checks.check("accuracy drop is the reason",
                 any("accuracy dropped" in reason for reason in bad["decision"]["reasons"]),
                 str(bad["decision"]["reasons"]))
    checks.check("rollback restores v1", bad["registry"]["active_version"] == "v1"
                 and bad["registry"]["traffic"]["v1"] == 1.0)
    checks.check("rollback is recorded in the history",
                 any("rollback" in entry["event"] for entry in bad["registry"]["history"]))
    held = result["held"]
    checks.check("healthy candidate during drift is held, not promoted",
                 held["outcome"] == "hold" and held["registry"]["active_version"] == "v1",
                 str(held["decision"]))
    checks.check("the hold is caused by drift, not quality",
                 bool(held["decision"]["drift_reasons"]) and not held["decision"]["quality_reasons"],
                 str(held["decision"]["reasons"]))
    checks.check("healthy candidate in a mild week is promoted", good["outcome"] == "promote"
                 and good["registry"]["active_version"] == "v2", str(good["decision"]))
    checks.check("healthy drop is inside the tolerance",
                 good["decision"]["accuracy_drop"] <= GATE["max_accuracy_drop"],
                 f"{good['decision']['accuracy_drop']:.3f}")
    checks.check("drift was measured on live data", 0.0 <= bad["drift"]["features"][0]["psi"], 
                 f"{bad['drift']['features'][0]['psi']:.3f}")
    checks.check("canary had enough labelled rows", bad["canary_rows"] >= GATE["min_canary_rows"])
    checks.check("both scenarios used the same gate", bad["gate"] == good["gate"])

    report = build_report(result)
    path = report.write(OUT_DIR, "report.md", measured_footer(result["environment"]))
    write_json(OUT_DIR, "incident.json", {
        "outcome": bad["outcome"], "reasons": bad["decision"]["reasons"],
        "registry": bad["registry"], "metrics": {"baseline": bad["baseline"],
                                                 "candidate": bad["candidate_metrics"]},
    })
    checks.check("report written", path.exists() and path.stat().st_size > 1200)
    checks.check("incident record written", (OUT_DIR / "incident.json").exists())
    return checks.report()


def main() -> int:
    parser = base_parser(__doc__ or "")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    result = run()
    print(build_report(result).render(measured_footer(result["environment"])))
    print(f"\nwritten: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
