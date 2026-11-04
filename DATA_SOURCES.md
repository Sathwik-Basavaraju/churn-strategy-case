# Data Sources

## Primary source — used for every number in this project

- **Dataset:** IBM Telco Customer Churn
- **URL used (downloaded with `curl` / `src/download_data.py`, not a browser):**
  `https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv`
- **Download date:** 2026-11-04
- **Verification on download:** 7,043 rows (plus header) × 21 columns:
  customerID, gender, SeniorCitizen, Partner, Dependents, tenure, PhoneService,
  MultipleLines, InternetService, OnlineSecurity, OnlineBackup, DeviceProtection,
  TechSupport, StreamingTV, StreamingMovies, Contract, PaperlessBilling,
  PaymentMethod, MonthlyCharges, TotalCharges, Churn.
  Raw churn rate 26.54% (1,869 churned / 7,043).
- **Local files:** `data/Telco-Customer-Churn.csv` (948 KB, the raw download,
  unchanged) and `data/cleaned.csv` (7,032 rows after dropping 11 blank-
  `TotalCharges` rows; see README).
- **Licence / note:** The IBM telco-churn sample dataset is distributed by IBM
  for teaching/demo use; this project reuses it for analysis only, with no
  customer-identifiable information beyond the dataset's own anonymised
  customerID values. No licence text ships in the mirror file itself, so none
  is reproduced here — check the source repository for current terms before
  commercial reuse.

## Substitution — none

No synthetic substitution was used. `src/generate_synthetic.py` is a fallback
generator (same 21 columns, invented churn propensities) that exists so the
pipeline can still be demonstrated if the IBM URL ever becomes unavailable.
It was **not** run for this project's results, and any future run that uses it
must state the substitution prominently in the README and in `metrics.json`
(`data_source.synthetic_substitution: true`) before publishing.
