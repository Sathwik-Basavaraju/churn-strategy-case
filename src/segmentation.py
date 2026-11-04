"""Customer segmentation with KMeans (scikit-learn only).

Features (all observed): tenure, MonthlyCharges, contract length
(Month-to-month=0, One year=1, Two year=2), n_services (count of
Yes across the six add-on services), Electronic check (0/1),
PaperlessBilling (0/1). StandardScaler, random_state=42, n_init=10.

k selection: silhouette score for k = 3..6, computed on the scaled
features; the k with the highest silhouette is chosen and the full
score table is saved in metrics.json so the choice is auditable.
Segments are labelled programmatically from their centroids and
dominant contract, not hand-named to fit a story.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

CONTRACT_LEN = {"Month-to-month": 0, "One year": 1, "Two year": 2}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "tenure": df["tenure"].astype(float),
        "MonthlyCharges": df["MonthlyCharges"].astype(float),
        "contract_length": df["Contract"].map(CONTRACT_LEN).astype(float),
        "n_services": df["n_services"].astype(float),
        "electronic_check": (df["PaymentMethod"] == "Electronic check").astype(float),
        "paperless": (df["PaperlessBilling"] == "Yes").astype(float),
    })


def describe_segment(sub: pd.DataFrame) -> str:
    tenure = sub["tenure"].mean()
    spend = sub["MonthlyCharges"].mean()
    contract = sub["Contract"].mode().iloc[0]
    tenure_band = "short-tenure" if tenure < 20 else (
        "mid-tenure" if tenure < 45 else "long-tenure")
    spend_band = "lower-spend" if spend < 55 else (
        "mid-spend" if spend < 70 else "higher-spend")
    return f"{tenure_band}, {spend_band}, mostly {contract}"


def run(df: pd.DataFrame, chart_path: Path) -> tuple[pd.DataFrame, dict]:
    feats = build_features(df)
    X = StandardScaler().fit_transform(feats)
    scores = {}
    for k in range(3, 7):
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
        scores[k] = float(silhouette_score(X, km.labels_))
    best_k = max(scores, key=scores.get)
    km = KMeans(n_clusters=best_k, random_state=42, n_init=10).fit(X)
    df = df.copy()
    df["segment"] = km.labels_
    rows = []
    for seg in sorted(df["segment"].unique()):
        sub = df[df["segment"] == seg]
        rows.append({
            "segment": int(seg),
            "label": describe_segment(sub),
            "n": int(len(sub)),
            "n_churned": int(sub["churn"].sum()),
            "churn_rate": float(sub["churn"].mean()),
            "mean_tenure": float(sub["tenure"].mean()),
            "mean_monthly_charges": float(sub["MonthlyCharges"].mean()),
            "dominant_contract": str(sub["Contract"].mode().iloc[0]),
            "share_month_to_month": float((sub["Contract"] == "Month-to-month").mean()),
            "mean_n_services": float(sub["n_services"].mean()),
        })
    # Chart: churn rate by segment
    seg_df = pd.DataFrame(rows).sort_values("churn_rate", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(seg_df["segment"].astype(str), seg_df["churn_rate"] * 100)
    ax.axhline(df["churn"].mean() * 100, color="red", linestyle="--",
               label=f"Overall churn {df['churn'].mean()*100:.1f}%")
    for i, v in enumerate(seg_df["churn_rate"] * 100):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center")
    ax.set_title("Churn rate by segment (KMeans, silhouette-chosen k)")
    ax.set_xlabel("Segment")
    ax.set_ylabel("Churn rate (%)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    info = {"k": int(best_k), "silhouette_scores": {str(k): v for k, v in scores.items()},
            "silhouette_best": float(scores[best_k]),
            "segments": rows}
    return df, info
