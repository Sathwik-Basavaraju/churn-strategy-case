"""Kaplan-Meier curves by contract + Cox proportional hazards (lifelines).

KM: one curve per Contract group, median survival = first month at
which survival <= 0.50 (lifelines ``median_survival_times_``); if a
group never drops to 0.50, median is reported as null (not reached).

Cox PH covariates (all observed, no invented fields): SeniorCitizen,
MonthlyCharges, Contract (One year / Two year vs Month-to-month),
InternetService Fiber optic vs other, PaperlessBilling, Electronic
check payment, TechSupport == "No". Concordance is lifelines'
``concordance_index_`` from the fitted model on this same data
(in-sample; no hold-out claim is made).

If lifelines is unavailable, this module raises ImportError and
run_all.py falls back to KM-only (manual pandas KM) with Cox
concordance = null. That fallback is NOT used in the shipped run:
lifelines 0.30.3 was installed and used.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def km_by_contract(df: pd.DataFrame, chart_path: Path) -> dict:
    from lifelines import KaplanMeierFitter
    kmf = KaplanMeierFitter()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    result: dict = {}
    for contract in ["Month-to-month", "One year", "Two year"]:
        sub = df[df["Contract"] == contract]
        kmf.fit(sub["duration"], event_observed=sub["event_observed"],
                label=contract)
        median = kmf.median_survival_time_
        # lifelines returns inf when survival never reaches 0.5
        median_val = None if (median == float("inf")) else float(median)
        result[contract] = {
            "n": int(len(sub)),
            "n_churned": int(sub["churn"].sum()),
            "churn_rate": float(sub["churn"].mean()),
            "median_survival_months": median_val,
            "survival_at_12m": float(kmf.survival_function_at_times(12).iloc[0]),
            "survival_at_24m": float(kmf.survival_function_at_times(24).iloc[0]),
        }
        kmf.plot_survival_function(ax=ax)
    ax.set_title("Kaplan-Meier survival by contract type\n"
                 "(tenure as time, non-churned right-censored at tenure)")
    ax.set_xlabel("Tenure (months)")
    ax.set_ylabel("Estimated survival (still a customer)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    return result


def cox_ph(df: pd.DataFrame) -> dict:
    from lifelines import CoxPHFitter
    cph_df = pd.DataFrame({
        "duration": df["duration"],
        "event_observed": df["event_observed"],
        "SeniorCitizen": df["SeniorCitizen"],
        "MonthlyCharges": df["MonthlyCharges"],
        "Contract_OneYear": (df["Contract"] == "One year").astype(int),
        "Contract_TwoYear": (df["Contract"] == "Two year").astype(int),
        "FiberOptic": (df["InternetService"] == "Fiber optic").astype(int),
        "PaperlessBilling": (df["PaperlessBilling"] == "Yes").astype(int),
        "ElectronicCheck": (df["PaymentMethod"] == "Electronic check").astype(int),
        "NoTechSupport": (df["TechSupport"] == "No").astype(int),
    })
    # Tenure 0 rows were already dropped in cleaning, so duration > 0.
    cph = CoxPHFitter()
    cph.fit(cph_df, duration_col="duration", event_col="event_observed")
    coefs = {}
    for var in cph.params_.index:
        coefs[str(var)] = {
            "coef": float(cph.params_[var]),
            "hazard_ratio": float(cph.hazard_ratios_[var]),
            "p_value": float(cph.summary.loc[var, "p"]),
        }
    return {
        "concordance": float(cph.concordance_index_),
        "n": int(len(cph_df)),
        "coefficients": coefs,
    }


def run(df: pd.DataFrame, chart_path: Path) -> dict:
    km = km_by_contract(df, chart_path)
    try:
        cox = cox_ph(df)
        cox_available = True
    except ImportError:
        cox = {"concordance": None, "coefficients": {}}
        cox_available = False
    return {"km_by_contract": km, "cox": cox,
            "cox_available": cox_available}
