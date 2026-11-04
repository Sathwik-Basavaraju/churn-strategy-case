"""Run the full pipeline end-to-end and write metrics.json + charts.

Run from the project folder:
    python3 src/run_all.py

Inputs:  data/Telco-Customer-Churn.csv (downloaded by
         src/download_data.py; already present in the shipped run)
Outputs: data/cleaned.csv
         outputs/metrics.json
         outputs/charts/km_by_contract.png
         outputs/charts/churn_by_segment.png
         outputs/charts/revenue_at_risk.png
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

# Allow running as `python3 src/run_all.py` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from clean_data import clean  # noqa: E402
from revenue_at_risk import run as revenue_run  # noqa: E402
from scenario_model import run as scenario_run  # noqa: E402
from segmentation import run as segment_run  # noqa: E402
from survival_analysis import run as survival_run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA_URL = ("https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
            "master/data/Telco-Customer-Churn.csv")


def main() -> None:
    raw_path = ROOT / "data" / "Telco-Customer-Churn.csv"
    if not raw_path.exists():
        raise SystemExit(
            f"Missing {raw_path}. Run: python3 src/download_data.py first.")
    raw = pd.read_csv(raw_path)
    df, clean_report = clean(raw)
    (ROOT / "data" / "cleaned.csv").write_text(
        df.to_csv(index=False), encoding="utf-8")

    survival = survival_run(df, ROOT / "outputs" / "charts" / "km_by_contract.png")
    df_seg, seg_info = segment_run(
        df, ROOT / "outputs" / "charts" / "churn_by_segment.png")
    revenue = revenue_run(
        df_seg, ROOT / "outputs" / "charts" / "revenue_at_risk.png")
    scenario = scenario_run(df_seg, revenue["highest_loss_segments"])

    metrics = {
        "project": "Customer Churn Strategy Case: Revenue-at-Risk Segmentation",
        "run_date": date.today().isoformat(),
        "data_source": {
            "name": "IBM Telco Customer Churn",
            "url": DATA_URL,
            "synthetic_substitution": False,
            "note": "Real IBM dataset downloaded from the IBM mirror; "
                    "no synthetic substitution was used.",
        },
        "method": {
            "cleaning": "TotalCharges coerced to numeric; rows with blank "
                        "TotalCharges dropped (see cleaning report).",
            "survival": "Kaplan-Meier by Contract (lifelines); tenure as time, "
                        "non-churned right-censored at tenure. Cox PH covariates "
                        "listed in src/survival_analysis.py; concordance is "
                        "in-sample.",
            "segmentation": "KMeans (scikit-learn, StandardScaler, "
                            "random_state=42, n_init=10); k chosen by "
                            "silhouette over k=3..6.",
            "revenue_at_risk": "Annualised = MonthlyCharges*12. Churned revenue "
                              "is realised lost run-rate; active at-risk = "
                              "non-churned in segments above overall churn rate.",
            "scenario": "See src/scenario_model.py assumptions; save rates "
                        "are ASSUMED scenarios, not observed outcomes.",
        },
        "cleaning": clean_report,
        "n_customers": clean_report["clean_n"],
        "n_churned": clean_report["n_churned"],
        "churn_rate": clean_report["churn_rate"],
        "survival": survival,
        "segmentation": seg_info,
        "revenue_at_risk": revenue,
        "scenario": scenario,
    }
    out = ROOT / "outputs" / "metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"n_customers={metrics['n_customers']:,}")
    print(f"n_churned={metrics['n_churned']:,}")
    print(f"churn_rate={metrics['churn_rate']:.4f}")
    print(f"Cox concordance={survival['cox']['concordance']}")
    print(f"KM by contract={json.dumps(survival['km_by_contract'], indent=2)}")
    print(f"Segments k={seg_info['k']} silhouette={seg_info['silhouette_best']:.4f}")
    for s in seg_info["segments"]:
        print(f"  seg {s['segment']}: n={s['n']} churn={s['churn_rate']:.3f} "
              f"label={s['label']}")
    print(f"Total churned annualised revenue=${revenue['total_churned_annualised_revenue']:,.0f}")
    print(f"At-risk actives: n={revenue['at_risk_active_n']:,} "
          f"annualised=${revenue['at_risk_active_annualised_revenue']:,.0f} "
          f"expected loss=${revenue['expected_loss_from_at_risk_actives']:,.0f}")
    print(f"Scenario blanket break-even={scenario['blanket_all_actives_in_top_segments']['break_even_save_rate']:.4f}")
    print(f"Scenario targeted break-even={scenario['targeted_month_to_month_in_top_segments']['break_even_save_rate']:.4f}")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
