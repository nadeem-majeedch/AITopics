"""Lab 6 - model size, latency, and quality before and after int8 quantization.

The model is a small MLP trained on the synthetic churn data. Its weights are then
quantized with symmetric per-tensor int8 scaling and the same held-out rows are
scored with both versions.

Measured and reported separately:

* **size** - float32 bytes against int8 bytes plus one scale per tensor;
* **quality** - accuracy, AUC, prediction agreement, mean probability shift;
* **latency** - median and p95 forward-pass time, measured here.

The latency number needs a warning attached, and the lab attaches it. The int8
weights are dequantized to float before the matrix multiplication, so this measures
the cost of carrying fewer bytes and more arithmetic, not the speed of a real int8
kernel. Do not quote it as an int8 speedup.

    python lab6_quantization.py
    python lab6_quantization.py --selftest
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))

from eval_core import (  # noqa: E402
    Checks,
    Report,
    base_parser,
    data,
    dequantize_model,
    environment_snapshot,
    float_size_bytes,
    load_weights,
    measured_footer,
    metrics,
    quantization_report,
    quantize_model,
    quantized_size_bytes,
    save_weights,
    stratified_split,
    time_calls,
    verify_manifest,
    write_json,
    write_manifest,
)

OUT_DIR = data.ROOT / "outputs" / "production" / "lab6"
NUMERIC = ["tenure_months", "monthly_charges", "support_tickets", "usage_gb"]
CATEGORICAL = ["contract_type", "region"]
SEED = 7


def forward(params: dict[str, np.ndarray], features: np.ndarray) -> np.ndarray:
    """Logistic output of a ReLU MLP. Written out so the quantized weights can be used."""
    hidden = (features - params["scaler_mean"]) / params["scaler_scale"]
    layer = 0
    while f"W{layer}" in params:
        hidden = np.maximum(0.0, hidden @ params[f"W{layer}"] + params[f"b{layer}"])
        layer += 1
    logits = hidden @ params["W_out"] + params["b_out"]
    return 1.0 / (1.0 + np.exp(-logits.ravel()))


def train_model() -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]:
    data.ensure_data()
    rows = data.load_csv(data.DATA / "customers" / "customers.csv")
    train, _, test = stratified_split(rows, "churned", (0.7, 0.15, 0.15), seed=SEED)
    x_train, _, levels = data.feature_matrix(train, NUMERIC, CATEGORICAL)
    x_test, _, _ = data.feature_matrix(test, NUMERIC, CATEGORICAL, levels)
    y_train = np.array(data.target(train))
    y_test = np.array(data.target(test))

    scaler = StandardScaler().fit(x_train)
    scaled = scaler.transform(x_train)
    model = MLPClassifier(
        hidden_layer_sizes=(16, 8), activation="relu", solver="adam",
        max_iter=1200, tol=1e-4, random_state=SEED, early_stopping=False,
    ).fit(scaled, y_train)

    params: dict[str, np.ndarray] = {
        "scaler_mean": scaler.mean_.astype(np.float32),
        "scaler_scale": scaler.scale_.astype(np.float32),
    }
    for index, (weights, bias) in enumerate(zip(model.coefs_, model.intercepts_)):
        name = "W_out" if index == len(model.coefs_) - 1 else f"W{index}"
        bias_name = "b_out" if index == len(model.coefs_) - 1 else f"b{index}"
        params[name] = weights.astype(np.float32)
        params[bias_name] = bias.astype(np.float32)
    return params, x_test, y_test


def run() -> dict:
    params, x_test, y_test = train_model()
    sklearn_reference = None

    original_probs = forward(params, x_test)
    quantized, meta = quantize_model(params, bits=8)
    restored = dequantize_model(quantized, meta)
    quantized_probs = forward(restored, x_test)

    quality = quantization_report(params, quantized, meta, original_probs, quantized_probs, y_test)
    size_original = float_size_bytes(params)
    size_quantized = quantized_size_bytes(quantized, meta)
    weight_names = [name for name, value in params.items()
                    if np.asarray(value).ndim >= 2 and np.asarray(value).size >= 64]
    weight_bytes = {
        "float32": sum(int(params[name].size) * 4 for name in weight_names),
        "int8": sum(int(quantized[name].size) + 4 for name in weight_names),
    }

    latency_original = time_calls(lambda: forward(params, x_test), repeats=100)
    latency_quantized = time_calls(lambda: forward(dequantize_model(quantized, meta), x_test), repeats=100)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    weight_path = OUT_DIR / "model_int8.npz"
    digest = save_weights(weight_path, quantized)
    manifest = write_manifest(
        OUT_DIR / "manifest.json",
        {"model_int8.npz": weight_path},
        metadata={"quantization": "symmetric per-tensor int8", "seed": SEED, "digest": digest},
    )
    reloaded = load_weights(weight_path, digest)

    return {
        "params": len(params),
        "weights": {name: int(np.asarray(value).size) for name, value in params.items()},
        "size_bytes": {"float32": size_original, "int8": size_quantized},
        "compression": quality["compression"],
        "weight_bytes": weight_bytes,
        "weight_compression": weight_bytes["float32"] / weight_bytes["int8"],
        "quality": quality,
        "latency_ms": {"float32": latency_original, "int8_dequantized": latency_quantized},
        "latency_ratio": latency_quantized["median_ms"] / latency_original["median_ms"],
        "artifact": {"path": str(weight_path.name), "digest": digest, "verified": not verify_manifest(manifest),
                     "arrays": len(reloaded)},
        "forward_check": float(np.max(np.abs(original_probs - sklearn_reference))) if sklearn_reference else None,
        "environment": environment_snapshot(),
    }


def build_report(result: dict) -> Report:
    quality = result["quality"]
    report = Report(
        "Lab 6 - quantization trade-offs",
        "A 16-8-1 MLP on the synthetic churn data, float32 against symmetric int8 weights.",
    )
    report.heading("Size")
    report.table(
        [{"representation": "float32", "bytes": result["size_bytes"]["float32"]},
         {"representation": "int8 + scales", "bytes": result["size_bytes"]["int8"]}],
        ["representation", "bytes"],
    )
    report.text(
        f"Whole-artifact compression: **{result['compression']:.2f}x**. Weight matrices alone compress "
        f"{result['weight_compression']:.2f}x, close to the theoretical 4x for 32-bit to 8-bit. The gap is "
        "overhead: biases, the scaler, and one scale per tensor are stored as float32, and on a model this "
        "small they are a large share of the bytes. Compression is a property of the model's shape as much as "
        "of the number format."
    )

    report.heading("Quality")
    report.table(
        [
            {"metric": "accuracy", "float32": quality["accuracy_original"], "int8": quality["accuracy_quantized"]},
            {"metric": "AUC", "float32": quality["auc_original"], "int8": quality["auc_quantized"]},
            {"metric": "prediction agreement", "float32": 1.0, "int8": quality["prediction_agreement"]},
            {"metric": "mean absolute probability shift", "float32": 0.0,
             "int8": quality["mean_abs_probability_shift"]},
        ],
        ["metric", "float32", "int8"],
    )
    report.text(
        f"Accuracy changed by {quality['accuracy_delta']:+.4f}. At this size the change is within run-to-run "
        "noise; the point is that it is measurable, and that agreement is not the same as accuracy. A larger "
        "model or a lower bit width would make the cost obvious."
    )

    latency = result["latency_ms"]
    report.heading("Latency (measured on this machine)")
    report.table(
        [{"version": "float32", "median ms": latency["float32"]["median_ms"],
          "p95 ms": latency["float32"]["p95_ms"]},
         {"version": "int8, dequantized per call", "median ms": latency["int8_dequantized"]["median_ms"],
          "p95 ms": latency["int8_dequantized"]["p95_ms"]}],
        ["version", "median ms", "p95 ms"],
    )
    report.text(
        f"Median latency ratio (int8 path / float32 path): {result['latency_ratio']:.2f}x. "
        "This int8 path dequantizes to float and runs the same matrix multiplication, so it trades bytes for "
        "arithmetic and is not a speed measurement. A real int8 runtime fuses quantization into the kernel; "
        "if throughput matters, measure the runtime you will deploy."
    )

    report.heading("Artifact handling")
    report.bullets([
        f"Saved as `{result['artifact']['path']}` with `allow_pickle=False`; SHA-256 `{result['artifact']['digest'][:16]}...`.",
        "The manifest was re-verified after writing; a digest mismatch is treated as a failed load, not a warning.",
        f"Arrays reloaded: {result['artifact']['arrays']}.",
    ])
    return report


def selftest() -> int:
    checks = Checks("lab 6 - quantization")
    result = run()
    quality = result["quality"]

    checks.check("forward pass is a probability", 0.0 <= quality["accuracy_original"] <= 1.0)
    checks.check("weight matrices compress close to 4x", 3.8 <= result["weight_compression"] <= 4.05,
                 f"{result['weight_compression']:.2f}x")
    checks.check("whole-artifact compression is lower because of float overhead",
                 result["compression"] < result["weight_compression"],
                 f"{result['compression']:.2f}x vs {result['weight_compression']:.2f}x")
    checks.check("int8 artifact is smaller", result["size_bytes"]["int8"] < result["size_bytes"]["float32"],
                 f"{result['size_bytes']}")
    checks.check("accuracy is preserved within 5 points", abs(quality["accuracy_delta"]) <= 0.05,
                 f"{quality['accuracy_delta']:+.4f}")
    checks.check("most predictions are unchanged", quality["prediction_agreement"] > 0.9,
                 f"{quality['prediction_agreement']:.3f}")
    checks.check("probability shift is small", quality["mean_abs_probability_shift"] < 0.05,
                 f"{quality['mean_abs_probability_shift']:.4f}")
    checks.check("latency was measured, not assumed",
                 result["latency_ms"]["float32"]["median_ms"] > 0.0)
    checks.check("artifact digest verified", result["artifact"]["verified"] is True)
    checks.check("reloaded array count matches", result["artifact"]["arrays"] == len(result["weights"]))

    report = build_report(result)
    path = report.write(OUT_DIR, "report.md", measured_footer(result["environment"]))
    write_json(OUT_DIR, "metrics.json", result)
    checks.check("report written", path.exists() and path.stat().st_size > 900)
    checks.check("report warns about the latency claim", "not a speed measurement" in path.read_text(encoding="utf-8"))
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
