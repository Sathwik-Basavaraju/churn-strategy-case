"""Fallback generator: a clearly-labelled synthetic IBM-like dataset.

Only used if the real IBM CSV cannot be downloaded. It reproduces the
same 21 columns, with plausible (invented, documented) churn patterns.
It must NEVER be presented as the real IBM data: run_all.py records
``data_source`` in metrics.json, and README/DATA_SOURCES describe any
substitution. In the run shipped with this project the real IBM file
was downloaded successfully, so this script was not used for results.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

COLUMNS = [
    "customerID", "gender", "SeniorCitizen", "Partner", "Dependents",
    "tenure", "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
    "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling",
    "PaymentMethod", "MonthlyCharges", "TotalCharges", "Churn",
]


def generate(n: int = 7043, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    contract = rng.choice(
        ["Month-to-month", "One year", "Two year"], size=n, p=[0.55, 0.21, 0.24])
    tenure = np.where(
        contract == "Month-to-month",
        rng.integers(0, 40, size=n),
        np.where(contract == "One year",
                 rng.integers(0, 60, size=n), rng.integers(0, 73, size=n)))
    monthly = np.round(rng.normal(65, 30, size=n).clip(18, 120), 2)
    # Invented synthetic churn propensity (NOT a real-data estimate).
    logit = -1.2 + 1.1 * (contract == "Month-to-month") - 0.02 * tenure
    prob = 1 / (1 + np.exp(-logit))
    churn = rng.random(n) < prob
    df = pd.DataFrame({
        "customerID": [f"{i:04d}-SYNTH" for i in range(n)],
        "gender": rng.choice(["Male", "Female"], size=n),
        "SeniorCitizen": rng.integers(0, 2, size=n),
        "Partner": rng.choice(["Yes", "No"], size=n),
        "Dependents": rng.choice(["Yes", "No"], size=n),
        "tenure": tenure,
        "PhoneService": "Yes",
        "MultipleLines": rng.choice(["Yes", "No"], size=n),
        "InternetService": rng.choice(["DSL", "Fiber optic", "No"], size=n),
        "OnlineSecurity": rng.choice(["Yes", "No"], size=n),
        "OnlineBackup": rng.choice(["Yes", "No"], size=n),
        "DeviceProtection": rng.choice(["Yes", "No"], size=n),
        "TechSupport": rng.choice(["Yes", "No"], size=n),
        "StreamingTV": rng.choice(["Yes", "No"], size=n),
        "StreamingMovies": rng.choice(["Yes", "No"], size=n),
        "Contract": contract,
        "PaperlessBilling": rng.choice(["Yes", "No"], size=n),
        "PaymentMethod": rng.choice(
            ["Electronic check", "Mailed check",
             "Bank transfer (automatic)", "Credit card (automatic)"], size=n),
        "MonthlyCharges": monthly,
        "TotalCharges": np.round(monthly * np.maximum(tenure, 1), 2),
        "Churn": np.where(churn, "Yes", "No"),
    })
    return df[COLUMNS]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/Telco-Customer-Churn-SYNTHETIC.csv")
    ap.add_argument("--n", type=int, default=7043)
    args = ap.parse_args()
    df = generate(args.n)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote SYNTHETIC dataset: {len(df):,} rows -> {args.out}")
    print(f"Synthetic churn rate: {(df['Churn'] == 'Yes').mean():.4f}")


if __name__ == "__main__":
    main()
