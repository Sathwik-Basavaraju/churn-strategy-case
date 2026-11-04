# Executive Memo — Customer Churn: Where the Revenue Is, and What to Offer

**Data:** IBM Telco Customer Churn, real dataset, 7,032 cleaned customers
(7,043 raw; 11 blank-`TotalCharges` rows dropped), 1,869 churned — **26.58%**.
Run date 2026-11-04. All figures computed by `src/run_all.py`; full audit trail
in `outputs/metrics.json`.

## Bottom line

Churn is concentrated in two segments. Do **not** launch a blanket discount.
A targeted offer to month-to-month customers in those segments is the better
shape — but even it does not break even at the save rates we assumed, so pilot
it cheaply (or with a non-price offer) and measure the real save rate before
scaling.

## 1. Where churn concentrates

- Month-to-month customers churn at **42.71%** (1,655 / 3,875), vs 11.28% on
  one-year and 2.85% on two-year contracts. Kaplan-Meier median survival is
  35 months for month-to-month; the longer contracts never drop to 50%
  survival in this snapshot. Cox PH (in-sample concordance **0.834**) puts the
  hazard ratio for a two-year contract at 0.027 and one-year at 0.161 vs
  month-to-month — contract is the dominant association.
- **Segment 2** (short-tenure, higher-spend, mostly month-to-month; n = 1,814,
  churn 52.98%) alone holds **$915,064 (54.8%)** of churned annualised revenue.
- **Segment 0** (short-tenure, mid-spend, mostly month-to-month; n = 1,238,
  churn 34.65%) holds a further **$356,894 (21.4%)**.
- Together: **$1,271,957 = 76.2% of the $1,669,570** total churned annualised
  revenue (Σ MonthlyCharges × 12 over churned customers).

## 2. Revenue still at risk

Active customers in those two above-average segments — the defined at-risk
population — number **1,662, worth $1,324,626 a year**. If they churned at
their segments' observed rates, the expected loss is **$598,250 a year**
($402,530 Segment 2 + $195,719 Segment 0). That is exposure under an
assumption, not a forecast: it assumes segment rates persist for actives.

## 3. Blanket vs targeted — the scenario (ASSUMPTIONS, not results)

Assumptions, stated plainly: **10% discount for 12 months, charged on every
customer offered; save rates of 10% / 15% / 20% of would-be churners assumed.**
Break-even save rate = discount ÷ cohort churn rate.

| Offer | Offered | Break-even save rate | Net @10% | Net @15% | Net @20% |
|---|---:|---:|---:|---:|---:|
| Blanket (all actives, Seg 2+0) | 1,662 | 21.96% | −$72,134 | −$41,970 | −$11,805 |
| **Targeted (month-to-month actives, Seg 2+0)** | **1,426** | **20.56%** | **−$59,734** | **−$31,438** | **−$3,142** |

Targeted wins at every assumed rate — at 20% it is only −$3,142 from break-even
vs −$11,805 blanket — because it concentrates spend on the 48.65%-churn
subgroup instead of the 45.54% blanket cohort. But "wins" still means "loses
money" at every assumed rate up to 20%.

## Recommendation

1. **Do not fund a blanket 10% discount** for Segments 2 + 0 on this evidence.
2. **Pilot a targeted offer** to month-to-month actives in Segments 2 + 0 only,
   preferably at a lower discount or with a non-price lever (TechSupport
   coverage is associated with a 1.63× hazard for customers without it;
   Fiber-optic and electronic-check customers also churn more — worth
   investigating *why* before discounting).
3. **Gate scale on a measured save rate above 20.6%** (the targeted break-even).
   If the pilot cannot clear that, the discount is destroying value even
   while "saving" customers.

## Caveats

Snapshot data, not a cohort study; in-sample concordance; segment rates
assumed to persist; save rates assumed, not observed; annualised revenue is a
run-rate (MonthlyCharges × 12), not lifetime value. See README Limitations.
