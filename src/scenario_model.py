"""Scenario model for the highest-loss segments: blanket vs targeted.

ASSUMPTIONS (not facts, not observed outcomes -- change them in
run_all.py / here and re-run):
- Discount: 10% off MonthlyCharges for 12 months (d = 0.10).
- Assumed save rates: 10%, 15%, 20% of would-be churners retained.
- Discount cost is charged on EVERY customer offered the deal for
  12 months (conservative: everyone who stays takes the discount).

Formulas, per cohort with N actives, segment churn rate r, mean
annual revenue A = mean(MonthlyCharges * 12):
- Expected churners without intervention = N * r
- Saved at save rate s = N * r * s
- Benefit = Saved * A
- Cost = N * d * A
- Net = Benefit - Cost
- Break-even save rate s* solves Benefit = Cost  =>  s* = d / r
  (independent of N and A -- a property of this cost model, stated
  explicitly so it can be challenged).

Cohorts:
- Blanket: ALL active customers in the highest-loss segments.
- Targeted: only Month-to-month active customers within those same
  segments (the highest-risk contract subgroup; their own churn rate
  r_targeted is computed from the data, so the targeted break-even
  is lower whenever r_targeted > r_blanket).

No result here claims a discount *will* save anyone: the save rates
are scenarios to compare, and the recommendation follows from which
cohort clears break-even at the lowest assumed save rate.
"""
from __future__ import annotations

DISCOUNT = 0.10
ASSUMED_SAVE_RATES = [0.10, 0.15, 0.20]


def cohort_stats(df: pd.DataFrame, mask) -> dict:
    sub = df[mask]
    active = sub[sub["churn"] == 0]
    n = len(active)
    # Churn rate of the full cohort (actives + churned) in this slice.
    r = float(sub["churn"].mean()) if len(sub) else 0.0
    a = float(active["annual_revenue"].mean()) if n else 0.0
    scenarios = {}
    for s in ASSUMED_SAVE_RATES:
        saved = n * r * s
        benefit = saved * a
        cost = n * DISCOUNT * a
        scenarios[f"{int(s*100)}%"] = {
            "assumed_save_rate": s,
            "saved_customers": float(saved),
            "benefit": float(benefit),
            "cost": float(cost),
            "net": float(benefit - cost),
        }
    return {
        "n_active_offered": int(n),
        "cohort_churn_rate": r,
        "mean_annual_revenue": a,
        "discount_fraction": DISCOUNT,
        "break_even_save_rate": float(DISCOUNT / r) if r else None,
        "scenarios": scenarios,
    }


def run(df: pd.DataFrame, highest_loss_segments: list[int]) -> dict:
    in_top = df["segment"].isin(highest_loss_segments)
    blanket = cohort_stats(df, in_top)
    targeted = cohort_stats(df, in_top & (df["Contract"] == "Month-to-month"))
    return {
        "highest_loss_segments": highest_loss_segments,
        "assumptions": {
            "discount_fraction": DISCOUNT,
            "discount_duration_months": 12,
            "discount_cost_applies_to": "every customer offered, for 12 months",
            "assumed_save_rates": ASSUMED_SAVE_RATES,
            "save_rate_definition": "share of would-be churners retained by the offer",
            "formula": "Net = N*r*s*A - N*d*A; break-even s* = d / r",
        },
        "blanket_all_actives_in_top_segments": blanket,
        "targeted_month_to_month_in_top_segments": targeted,
    }
