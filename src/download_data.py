"""Download the IBM Telco Customer Churn CSV from a public mirror.

Default URL (IBM's own mirror repo):
    https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv

Usage:
    python3 src/download_data.py [--url URL] [--out data/Telco-Customer-Churn.csv]

The script verifies the download: expected 21 columns including
``customerID`` and ``Churn``, and prints row count and churn rate.
It does not invent data: if the download fails it exits non-zero and
prints the error, so the caller can fall back to the synthetic
generator (src/generate_synthetic.py) and document that substitution.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import requests

DEFAULT_URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
    "master/data/Telco-Customer-Churn.csv"
)
EXPECTED_COLUMNS = [
    "customerID", "gender", "SeniorCitizen", "Partner", "Dependents",
    "tenure", "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
    "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling",
    "PaymentMethod", "MonthlyCharges", "TotalCharges", "Churn",
]


def download(url: str, out: Path) -> pd.DataFrame:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(resp.content)
    df = pd.read_csv(out)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Downloaded CSV missing columns: {missing}")
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--out", default="data/Telco-Customer-Churn.csv")
    args = ap.parse_args()
    out = Path(args.out)
    try:
        df = download(args.url, out)
    except Exception as exc:  # noqa: BLE001 - report honestly, exit non-zero
        print(f"DOWNLOAD FAILED: {exc}", file=sys.stderr)
        return 1
    churn_rate = (df["Churn"] == "Yes").mean()
    print(f"Downloaded {len(df):,} rows x {len(df.columns)} columns -> {out}")
    print(f"Churn rate (raw): {churn_rate:.4f} "
          f"({(df['Churn'] == 'Yes').sum():,} churned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
