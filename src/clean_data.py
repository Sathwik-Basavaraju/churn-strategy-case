"""Clean the IBM Telco churn CSV.

Rules (all visible here, no hidden imputations):
- ``TotalCharges`` is coerced to numeric; rows where it is blank
  (11 rows in the downloaded file, all with tenure 0) are dropped,
  because a tenure-0 customer has no observed tenure window.
- ``churn`` = 1 if Churn == "Yes" else 0.
- ``duration`` = tenure (months); ``event_observed`` = churn.
  LIMITATION: the IBM file is a cross-sectional snapshot, not a
  longitudinal follow-up study. Survival analysis here treats tenure
  as time-to-event with non-churned customers right-censored at their
  tenure. That is a standard teaching approximation for this dataset,
  not a true cohort survival estimate.
- ``annual_revenue`` = MonthlyCharges * 12.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SERVICE_COLS = ["OnlineSecurity", "OnlineBackup", "DeviceProtection",
                "TechSupport", "StreamingTV", "StreamingMovies"]


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    raw_n = len(df)
    df = df.copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    n_blank_total = int(df["TotalCharges"].isna().sum())
    df = df.dropna(subset=["TotalCharges"])
    df["churn"] = (df["Churn"] == "Yes").astype(int)
    df["duration"] = df["tenure"].astype(int)
    df["event_observed"] = df["churn"]
    df["annual_revenue"] = df["MonthlyCharges"] * 12
    df["n_services"] = sum((df[c] == "Yes").astype(int) for c in SERVICE_COLS)
    report = {
        "raw_n": int(raw_n),
        "dropped_blank_total_charges": int(n_blank_total),
        "clean_n": int(len(df)),
        "n_churned": int(df["churn"].sum()),
        "churn_rate": float(df["churn"].mean()),
    }
    return df, report


def main() -> None:
    raw = Path("data/Telco-Customer-Churn.csv")
    out = Path("data/cleaned.csv")
    df = pd.read_csv(raw)
    cleaned, report = clean(df)
    out.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(out, index=False)
    print(report)
    print(f"Wrote {len(cleaned):,} rows -> {out}")


if __name__ == "__main__":
    main()
