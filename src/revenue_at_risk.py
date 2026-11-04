"""Revenue at risk, defined precisely (no vague 'at-risk' bucket).

Definitions used in code, README and the executive memo:
- Annualised revenue of a customer = MonthlyCharges * 12.
- Realised churned annualised revenue (per segment) = sum of
  annualised revenue over customers in that segment who churned.
  This is revenue already lost in the snapshot, expressed at an
  annual run-rate -- it is NOT a forecast.
- Active at-risk customers = non-churned customers in segments whose
  churn rate is ABOVE the overall churn rate. Their gross annualised
  revenue is 'active at-risk revenue' (exposure, not a loss).
- Expected annual loss from those actives, at segment churn rate =
  sum over at-risk segments of (active annualised revenue * segment
  churn rate). This assumes actives in a segment churn at that
  segment's observed rate -- an assumption, stated as such.

The 'highest-loss segments' for the scenario model are the top 2
segments by realised churned annualised revenue.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def run(df: pd.DataFrame, chart_path: Path) -> dict:
    overall_rate = float(df["churn"].mean())
    rows = []
    for seg in sorted(df["segment"].unique()):
        sub = df[df["segment"] == seg]
        churned = sub[sub["churn"] == 1]
        active = sub[sub["churn"] == 0]
        rows.append({
            "segment": int(seg),
            "n": int(len(sub)),
            "n_churned": int(len(churned)),
            "churn_rate": float(sub["churn"].mean()),
            "churned_annualised_revenue": float(churned["annual_revenue"].sum()),
            "active_n": int(len(active)),
            "active_annualised_revenue": float(active["annual_revenue"].sum()),
        })
    total_churned_rev = sum(r["churned_annualised_revenue"] for r in rows)
    for r in rows:
        r["share_of_churned_revenue"] = (
            r["churned_annualised_revenue"] / total_churned_rev
            if total_churned_rev else 0.0)
        r["is_at_risk_segment"] = bool(r["churn_rate"] > overall_rate)
        r["expected_loss_from_actives"] = (
            r["active_annualised_revenue"] * r["churn_rate"]
            if r["is_at_risk_segment"] else 0.0)
    at_risk = [r for r in rows if r["is_at_risk_segment"]]
    ranked = sorted(rows, key=lambda r: r["churned_annualised_revenue"],
                    reverse=True)
    highest_loss_segments = [r["segment"] for r in ranked[:2]]

    # Chart: churned vs active-at-risk annualised revenue by segment
    plot_df = pd.DataFrame(rows).sort_values(
        "churned_annualised_revenue", ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = range(len(plot_df))
    ax.bar(x, plot_df["churned_annualised_revenue"] / 1e6,
           label="Churned annualised revenue (lost, run-rate)")
    ax.bar(x, [r["expected_loss_from_actives"] / 1e6 if r["is_at_risk_segment"]
               else 0 for r in plot_df.to_dict("records")],
           bottom=plot_df["churned_annualised_revenue"] / 1e6,
           label="Expected loss from actives (segment churn rate)")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"Seg {s}" for s in plot_df["segment"]])
    ax.set_title("Revenue at risk by segment ($m, annualised)")
    ax.set_ylabel("$m per year")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)

    return {
        "overall_churn_rate": overall_rate,
        "total_churned_annualised_revenue": float(total_churned_rev),
        "total_active_annualised_revenue": float(df[df["churn"] == 0]["annual_revenue"].sum()),
        "at_risk_active_n": int(sum(r["active_n"] for r in at_risk)),
        "at_risk_active_annualised_revenue": float(
            sum(r["active_annualised_revenue"] for r in at_risk)),
        "expected_loss_from_at_risk_actives": float(
            sum(r["expected_loss_from_actives"] for r in at_risk)),
        "highest_loss_segments": highest_loss_segments,
        "segments": rows,
    }
