"""Generate the small synthetic datasets used by the foundation labs.

The datasets contain no real people, are deterministic for a given seed, and
are released with the course under CC0-1.0. Generated CSV files are written to
``datasets/foundations/generated/`` and are intentionally excluded from Git.

Usage:
    python scripts/make_foundation_data.py
    python scripts/make_foundation_data.py --out-dir datasets/foundations/generated --seed 42
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

NEIGHBOURHOOD_EFFECT = {"north": 35_000, "south": -10_000, "east": 15_000, "west": -5_000}
COURSE_EFFECT = {"Math": 0.2, "Physics": 0.0, "CS": 0.45}


def make_house_prices(n: int = 600, seed: int = 42) -> pd.DataFrame:
    """Return a synthetic house-price table with a nonlinear price surface."""
    rng = np.random.default_rng(seed)
    area = rng.normal(1_800, 500, n).clip(600, 4_000)
    bedrooms = rng.integers(1, 6, n)
    age = rng.integers(0, 60, n)
    distance_km = rng.gamma(2.0, 2.0, n).clip(0.5, 25.0)
    garage = rng.integers(0, 2, n)
    neighbourhood = rng.choice(list(NEIGHBOURHOOD_EFFECT), n, p=[0.3, 0.25, 0.25, 0.2])

    base = (
        120_000
        + 95 * area
        + 18_000 * bedrooms
        - 900 * age
        - 4_500 * distance_km
        + 12_000 * garage
        + 0.00004 * area**2
    )
    location = pd.Series(neighbourhood).map(NEIGHBOURHOOD_EFFECT).to_numpy()
    noise = rng.normal(0, 20_000, n)
    price = (base + location + noise).clip(50_000, None)

    return pd.DataFrame(
        {
            "area_sqft": area.round(1),
            "bedrooms": bedrooms,
            "age_years": age,
            "distance_km": distance_km.round(2),
            "garage": garage,
            "neighbourhood": neighbourhood,
            "sale_price": price.round(0),
        }
    )


def make_student_performance(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """Return a synthetic student table with a binary pass outcome."""
    rng = np.random.default_rng(seed)
    study_hours = rng.gamma(2.0, 2.0, n).clip(0, 20)
    attendance = rng.uniform(40, 100, n)
    prior_score = rng.normal(65, 12, n).clip(0, 100)
    sleep_hours = rng.normal(7, 1.2, n).clip(3, 10)
    tutoring = rng.choice(["yes", "no"], n, p=[0.35, 0.65])
    course = rng.choice(list(COURSE_EFFECT), n, p=[0.4, 0.3, 0.3])

    logit = (
        -11.5
        + 0.30 * study_hours
        + 0.055 * attendance
        + 0.075 * prior_score
        + 0.20 * sleep_hours
        + 1.1 * (tutoring == "yes")
        + pd.Series(course).map(COURSE_EFFECT).to_numpy()
    )
    probability = 1 / (1 + np.exp(-logit))
    passed = rng.binomial(1, probability)
    final_score = (
        15
        + 2.6 * study_hours
        + 0.30 * attendance
        + 0.40 * prior_score
        + 0.8 * sleep_hours
        + 4.0 * (tutoring == "yes")
        + 3.0 * pd.Series(course).map(COURSE_EFFECT).to_numpy()
        + rng.normal(0, 5, n)
    ).clip(0, 100)

    return pd.DataFrame(
        {
            "study_hours": study_hours.round(2),
            "attendance": attendance.round(1),
            "prior_score": prior_score.round(1),
            "sleep_hours": sleep_hours.round(2),
            "tutoring": tutoring,
            "course": course,
            "passed": passed,
            "final_score": final_score.round(1),
        }
    )


def make_student_performance_messy(n: int = 500, seed: int = 43) -> pd.DataFrame:
    """Add missing values, duplicates, and inconsistent categories for F04."""
    clean = make_student_performance(n=n, seed=seed)
    messy = clean.copy()
    rng = np.random.default_rng(seed + 100)

    for column, fraction in {
        "attendance": 0.07,
        "prior_score": 0.05,
        "sleep_hours": 0.09,
    }.items():
        index = rng.choice(len(messy), size=int(len(messy) * fraction), replace=False)
        messy.loc[index, column] = np.nan

    course_index = rng.choice(len(messy), size=25, replace=False)
    messy.loc[course_index, "course"] = rng.choice([" math ", "MATH", "physics", "CS "], 25)
    tutoring_index = rng.choice(len(messy), size=20, replace=False)
    messy.loc[tutoring_index, "tutoring"] = rng.choice(["Yes", "NO", "yes "], 20)

    duplicates = messy.sample(10, random_state=seed)
    messy = pd.concat([messy, duplicates], ignore_index=True)
    return messy.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def make_customer_segments(n: int = 420, seed: int = 42) -> pd.DataFrame:
    """Return unlabeled-looking customer data with a withheld latent segment."""
    rng = np.random.default_rng(seed)
    latent = rng.choice([0, 1, 2], n, p=[0.4, 0.35, 0.25])
    spend = np.choose(latent, [180, 650, 1_200]) + rng.normal(0, 60, n)
    visits = np.choose(latent, [2.0, 8.0, 18.0]) + rng.normal(0, 1.5, n)
    age = np.choose(latent, [24, 38, 52]) + rng.normal(0, 4, n)
    online_share = np.choose(latent, [0.8, 0.45, 0.2]) + rng.normal(0, 0.08, n)

    return pd.DataFrame(
        {
            "annual_spend": spend.round(2).clip(20, None),
            "visits_per_month": visits.round(1).clip(0.2, None),
            "age": age.round(0).clip(18, 80).astype(int),
            "online_share": online_share.round(3).clip(0, 1),
            "latent_segment": latent,
        }
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65_536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("datasets/foundations/generated"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    tables = {
        "house_prices": make_house_prices(seed=args.seed),
        "student_performance": make_student_performance(seed=args.seed),
        "student_performance_messy": make_student_performance_messy(seed=args.seed + 1),
        "customer_segments": make_customer_segments(seed=args.seed),
    }

    manifest = {}
    for name, frame in tables.items():
        path = args.out_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        manifest[name] = {
            "rows": int(frame.shape[0]),
            "columns": int(frame.shape[1]),
            "sha256": sha256(path),
        }
        print(f"{path}  shape={frame.shape}  sha256={manifest[name]['sha256'][:16]}...")

    manifest_path = args.out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path}")
    print("Synthetic data: no real people; course release is CC0-1.0.")


if __name__ == "__main__":
    main()
