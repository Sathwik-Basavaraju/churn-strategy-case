# Customer Churn Strategy Case: Revenue-at-Risk Segmentation

**Stack:** Python, lifelines, scikit-learn · **Data:** IBM Telco Customer Churn (real dataset, see below)
**Run date:** 2026-11-04 · **All figures below are computed by `src/run_all.py` from the actual data and match `outputs/metrics.json`. No figure is copied from a brief or placeholder.**

## The story in one paragraph

Churn is concentrated, not diffuse. Of 7,032 cleaned customers, 1,869 churned (26.58%).
Two KMeans segments — Segment 2 and Segment 0, both short-tenure and mostly
month-to-month — account for **$1,271,957 of the $1,669,570 churned annualised
revenue (76.2%)**. A 10%-for-12-months discount does **not** pay for itself at
any assumed save rate up to 20% under the cost model in this project, for either
a blanket or a targeted offer — but targeting month-to-month customers inside
those two segments loses far less than blanketing them, and is the only offer
shape worth piloting (see the executive memo).

## Data source — no substitution

- **Dataset:** IBM Telco Customer Churn, downloaded 2026-11-04 from the IBM mirror:
  `https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv`
- **Raw file:** 7,043 rows × 21 columns (`data/Telco-Customer-Churn.csv`, 948 KB).
- **Cleaning:** `TotalCharges` coerced to numeric; **11 rows with blank
  `TotalCharges` (all tenure 0) dropped** → **cleaned n = 7,032**
  (`data/cleaned.csv`). Raw churn rate 26.54% (1,869 / 7,043); cleaned churn
  rate **26.58% (1,869 / 7,032)**. The 11 dropped rows were all non-churned, so
  the churned count is unchanged.
- **No synthetic data was used.** `src/generate_synthetic.py` exists only as a
  documented fallback if the download ever fails; it was not used for any
  number in this project. Full provenance in `DATA_SOURCES.md`.

## How to run

```bash
pip install -r requirements.txt
python3 src/download_data.py   # already downloaded in the shipped run; re-verifies row count / churn rate
python3 src/run_all.py         # cleans, fits KM + Cox, segments, prices revenue at risk, runs scenarios
python3 -m py_compile src/*.py
```

Outputs: `outputs/metrics.json`, `outputs/charts/*.png`, `data/cleaned.csv`.

## Method

1. **Survival (lifelines).** Tenure (months) as time-to-event; churned = event,
   non-churned = right-censored at tenure. Kaplan-Meier by Contract; Cox PH with
   covariates SeniorCitizen, MonthlyCharges, Contract (One/Two year vs
   month-to-month), Fiber optic, PaperlessBilling, Electronic check, No TechSupport.
   Concordance is **in-sample** (no hold-out claim).
2. **Segmentation (scikit-learn only).** KMeans on StandardScaler-scaled tenure,
   MonthlyCharges, contract length (0/1/2), number of add-on services, electronic
   check, paperless billing; `random_state=42`, `n_init=10`. k chosen by silhouette
   over k = 3–6.
3. **Revenue at risk (defined, not vague).** Annualised revenue = MonthlyCharges × 12.
   *Churned annualised revenue* = sum over churned customers (realised lost
   run-rate, not a forecast). *Active at-risk* = non-churned customers in segments
   whose churn rate exceeds the overall rate; *expected loss* = their annualised
   revenue × their segment's churn rate (an assumption, stated as such).
4. **Scenario model.** Highest-loss segments = top 2 by churned annualised revenue.
   Blanket = all actives in those segments; targeted = only month-to-month actives
   inside them. Discount **assumption: 10% off for 12 months, charged on every
   customer offered**. Save rates **assumed: 10% / 15% / 20%** of would-be churners
   retained — these are scenarios, not observed outcomes.
   Formula: Net = N·r·s·A − N·d·A, so break-even save rate s\* = d / r.

## Results (computed, 2026-11-04 run)

### Survival by contract

| Contract | n | Churned | Churn rate | KM median survival | Survival @12m | Survival @24m |
|---|---:|---:|---:|---:|---:|---:|
| Month-to-month | 3,875 | 1,655 | 42.71% | 35 months | 70.3% | 58.6% |
| One year | 1,472 | 166 | 11.28% | not reached (>50% survive) | 99.1% | 97.8% |
| Two year | 1,685 | 48 | 2.85% | not reached (>50% survive) | 100.0% | 100.0% |

**Cox PH concordance (in-sample, lifelines 0.30.3): 0.834.**
Hazard ratios: Two year contract 0.027, One year 0.161, Fiber optic 3.02,
Electronic check 1.65, No TechSupport 1.63, PaperlessBilling 1.19,
SeniorCitizen 0.87, MonthlyCharges 0.978 per $1 (all p < 0.02; full table in
`metrics.json`). Contract dominates: moving a customer off month-to-month is
associated with a far larger hazard reduction than any single service feature.

### Segmentation — k = 6 (silhouette 0.312; k=3: 0.287, k=4: 0.301, k=5: 0.306)

| Seg | Label | n | Churn rate | Mean tenure | Mean $/mo | Churned annualised revenue | Share of churned revenue |
|---:|---|---|---:|---:|---:|---:|---:|
| 2 | short-tenure, higher-spend, mostly Month-to-month | 1,814 | 52.98% | 19.0 mo | $76.94 | $915,064 | 54.8% |
| 0 | short-tenure, mid-spend, mostly Month-to-month | 1,238 | 34.65% | 18.4 mo | $62.04 | $356,894 | 21.4% |
| 4 | short-tenure, lower-spend, mostly Month-to-month | 1,116 | 22.94% | 12.6 mo | $39.63 | $145,936 | 8.7% |
| 1 | long-tenure, higher-spend, mostly Two year | 1,213 | 12.20% | 59.6 mo | $91.50 | $176,717 | 10.6% |
| 5 | long-tenure, mid-spend, mostly Two year | 784 | 8.29% | 54.3 mo | $81.37 | $71,578 | 4.3% |
| 3 | long-tenure, lower-spend, mostly Two year | 867 | 1.15% | 48.2 mo | $23.38 | $3,382 | 0.2% |

### Revenue at risk

- **Total churned annualised revenue: $1,669,570**
  = Σ (MonthlyCharges × 12) over the 1,869 churned customers (verified
  independently from `data/cleaned.csv`). Rounded, that is $1.67M — the only
  headline figure from the original brief that this run reproduces, and it is
  shown here with its calculation, not copied.
- **Active at-risk (Segments 2 + 0 only, the segments above the 26.58% overall
  rate): 1,662 customers, $1,324,626 annualised revenue, $598,250 expected loss**
  at their segment churn rates ($402,530 from Segment 2 + $195,719 from Segment 0).
- Total active annualised revenue (all segments): $3,798,362.

### Scenario: 10% discount for 12 months (assumed save rates, not observed)

| Cohort | Actives offered | Cohort churn rate | Break-even save rate (d/r) | Net @10% saved | Net @15% saved | Net @20% saved |
|---|---:|---:|---:|---:|---:|---:|
| Blanket (all actives, Seg 2+0) | 1,662 | 45.54% | **21.96%** | −$72,134 | −$41,970 | −$11,805 |
| Targeted (month-to-month actives, Seg 2+0) | 1,426 | 48.65% | **20.56%** | −$59,734 | −$31,438 | −$3,142 |

**Reading:** neither offer breaks even at an assumed save rate of 20% or below,
because break-even (20.6% targeted, 22.0% blanket) sits above the highest assumed
rate. Targeted is strictly better at every assumed rate (it saves ~139 customers
at 20% vs ~151 blanket, but costs $116,327 vs $132,463). The honest recommendation
is therefore *targeted over blanket, and pilot only with a cheaper offer or with
evidence of a >20.6% save rate* — not a blanket discount launch.

### Reconciliation with the original brief's figures

This run does **not** reproduce several figures that appeared in the original
brief, so they are **not** used as results anywhere in this project:

- The brief's concordance figure does not match this run's **0.834** (different
  covariate set, cleaned n = 7,032, in-sample lifelines fit — the brief's model
  specification was not available to reproduce exactly).
- The brief's overall churn figure does not match this run's **26.54% raw /
  26.58% cleaned**.
- The brief's single scenario net figure does not match any net in the table
  above (this run's nets range from −$72,134 to −$3,142 across cohorts and
  assumed save rates, under the stated 10%-on-every-offered-customer cost model).
- The brief's $1.67M-style total **does** round-match this run's computed
  **$1,669,570** (calculation shown above).

## Charts

- `outputs/charts/km_by_contract.png` — Kaplan-Meier curves by contract
- `outputs/charts/churn_by_segment.png` — churn rate by segment vs overall
- `outputs/charts/revenue_at_risk.png` — churned + expected-loss revenue by segment

## Limitations (read before citing)

- The IBM file is a **cross-sectional snapshot, not a longitudinal cohort**:
  KM/Cox treat tenure as time-to-event with censoring, which is a teaching
  approximation. The Two-year 100% survival at 12/24 months reflects the
  snapshot's tenure structure, not a guarantee.
- Cox concordance is **in-sample**; no out-of-sample predictive claim is made.
- KMeans segments are descriptive, not causal: segment membership does not
  *cause* churn, and the silhouette (0.312) is modest — segments overlap.
- Annualised revenue uses MonthlyCharges × 12 and ignores tenure already
  served, taxes, and acquisition cost; it is a run-rate, not lifetime value.
- Save rates and discount cost are **assumptions**. A real decision needs a
  pilot that measures the actual save rate before scaling any discount.
