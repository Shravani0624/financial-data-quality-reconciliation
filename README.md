# Financial Data Quality & Reconciliation Pipeline

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![SQL](https://img.shields.io/badge/SQL-4479A1?style=flat&logo=postgresql&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white) ![ETL](https://img.shields.io/badge/ETL-14b8a6?style=flat)

**Portfolio:** https://shravani0624.github.io/portfolio/ | **Profile:** https://github.com/Shravani0624


## Data notice
**All data in this project is SYNTHETIC, generated for demonstration.**
It is not Pinevox data, not TCS data, and not any employer's real data.
Issues (duplicates, breaks, outliers) are deliberately planted so the
pipeline has realistic audit work to find.

## Problem
Daily financial and operational reporting is only trustworthy if the
underlying transactions reconcile to department logs. A daily audit must
catch duplicates, missing values, invalid codes, outliers and
reconciliation breaks before reports go to stakeholders.

## Method
`pipeline.py` (Python + Pandas) loads the synthetic transactions and
department logs, then runs **14 daily-audit checks**:

1. Duplicate transaction ID
2. Null amount
3. Null department
4. Negative amount
5. Zero amount
6. Future date (after the January 2026 window)
7. Orphan department (not on the master department list)
8. Invalid status
9. Missing account ID
10. Amount over 3x the department median
11. Possible double-posting (same date, account and amount)
12. Weekend posting, flagged for review only, not treated as an error
13. Missing date
14. Unknown category

It then reconciles transaction totals against department log totals by
date and department, and summarises variance by department.
`sql/analysis.sql` shows the same thinking in SQL: CTEs, window-function
rolling averages, ranking, and department share of total.

## Verified run results
Run with `python pipeline.py` (verified October 2026):

- Transactions reviewed: **600**
- Department log rows: **150**
- Audit checks run: **14**
- Total discrepancy flags: **174**, of which 161 are weekend-posting
  review flags; the remaining 13 are error-type flags (duplicates,
  null/negative/zero amounts, orphan department, invalid status,
  missing account, outlier, unknown category, future date)
- Reconciliation rows: **152**; balanced: **128**; breaks: **24**
- Total transaction amount: **1,652,594.76**
- Total log amount: **1,648,215.83**
- Three checks returned 0 in this seed (null department, possible
  double-posting, missing date). They are kept because a daily audit
  should still check for them.

## How to run
```bash
pip install -r requirements.txt
python pipeline.py
```
Outputs are written to `output/`:
`discrepancy_log.csv`, `reconciliation_report.csv`,
`department_variance.csv`, `reconciliation_report.md`.

## Skills shown
SQL (CTEs, window functions), Python (Pandas), ETL, data quality
assessment, reconciliation, variance analysis, financial reporting.
