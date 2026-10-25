"""
Financial Data Quality & Reconciliation Pipeline.
SYNTHETIC DATA ONLY: generated for demonstration. Not Pinevox or TCS real data.
Reads data/transactions.csv and data/department_logs.csv, runs 14 daily-audit
checks, and writes a discrepancy log, a reconciliation report and a
department variance report to output/.

Run:  python pipeline.py
Requires: pandas
"""
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)


def check(name, df):
    """Return a one-row summary dict for a filtered discrepancy dataframe."""
    return {"check": name, "records_flagged": int(len(df)),
            "example_ids": ", ".join(str(x) for x in df["transaction_id"].head(5)) if len(df) else ""}


def main():
    tx = pd.read_csv(BASE / "data" / "transactions.csv", parse_dates=["date"])
    logs = pd.read_csv(BASE / "data" / "department_logs.csv", parse_dates=["date"])
    # Master department list: a department in transactions but not here is an orphan.
    valid_depts = {"Finance", "Operations", "Sales", "Inventory", "HR"}
    issues = []

    # 1 duplicates, 2 null amount, 3 null department, 4 negative amount,
    # 5 zero amount, 6 future date, 7 orphan department, 8 invalid status,
    # 9 missing account, 10 amount outlier (>3x dept median), 11 duplicate
    # amount+date+account (possible double-posting), 12 weekend posting
    # flagged for review, 13 missing date, 14 non-numeric-safe category.
    dup = tx[tx.duplicated("transaction_id", keep=False)].sort_values("transaction_id")
    issues.append(check("duplicate_transaction_id", dup))
    issues.append(check("null_amount", tx[tx["amount"].isna()]))
    issues.append(check("null_department", tx[tx["department"].isna()]))
    issues.append(check("negative_amount", tx[tx["amount"] < 0]))
    issues.append(check("zero_amount", tx[tx["amount"] == 0]))
    issues.append(check("future_date", tx[tx["date"] > pd.Timestamp("2026-01-31")]))
    issues.append(check("orphan_department_not_in_logs", tx[~tx["department"].isin(valid_depts)]))
    issues.append(check("invalid_status", tx[~tx["status"].isin(["posted", "pending", "reversed"])]))
    issues.append(check("missing_account_id", tx[tx["account_id"].isna()]))
    med = tx.groupby("department")["amount"].transform("median")
    issues.append(check("amount_over_3x_department_median", tx[tx["amount"] > 3 * med]))
    dbl = tx[tx.duplicated(["date", "account_id", "amount"], keep=False)]
    issues.append(check("possible_double_posting_same_date_account_amount", dbl))
    issues.append(check("weekend_posting_for_review", tx[tx["date"].dt.weekday >= 5]))
    issues.append(check("missing_date", tx[tx["date"].isna()]))
    issues.append(check("unknown_category", tx[~tx["category"].isin(
        ["sales", "refund", "payroll", "supplies", "rent", "services"])]))

    summary = pd.DataFrame(issues)
    summary.to_csv(OUT / "discrepancy_log.csv", index=False)

    # Reconciliation: transaction totals vs department daily-log totals.
    tx_tot = tx.groupby(["date", "department"], dropna=False)["amount"].sum().reset_index()
    rec = logs.merge(tx_tot, on=["date", "department"], how="outer",
                     suffixes=("_log", "_transactions"))
    rec["amount_log"] = rec["amount_log"].fillna(0)
    rec["amount_transactions"] = rec["amount_transactions"].fillna(0)
    rec["difference"] = rec["amount_transactions"] - rec["amount_log"]
    rec["status"] = rec["difference"].apply(lambda d: "balanced" if d == 0 else "break")
    rec = rec.sort_values(["date", "department"])
    rec.to_csv(OUT / "reconciliation_report.csv", index=False)

    # Variance: transactions vs log totals by department.
    var = rec.groupby("department").agg(
        log_total=("amount_log", "sum"), transaction_total=("amount_transactions", "sum"),
        breaks=("status", lambda s: int((s == "break").sum())),
        days=("date", "nunique")).reset_index()
    var["variance"] = var["transaction_total"] - var["log_total"]
    var["variance_pct"] = (var["variance"].astype(float) / var["log_total"].astype(float).replace(0, float("nan")) * 100).round(2)
    var.to_csv(OUT / "department_variance.csv", index=False)

    total_flagged = int(summary["records_flagged"].sum())
    breaks = int((rec["status"] == "break").sum())
    report = (
        "# Reconciliation Report (SYNTHETIC DATA)\n\n"
        f"- Transactions reviewed: {len(tx)}\n"
        f"- Department log rows: {len(logs)}\n"
        f"- Audit checks run: {len(summary)}\n"
        f"- Total discrepancy flags (a record can appear in more than one check): {total_flagged}\n"
        f"- Reconciliation rows: {len(rec)}, balanced: {len(rec) - breaks}, breaks: {breaks}\n"
        f"- Total transaction amount: {tx['amount'].sum():,.2f}\n"
        f"- Total log amount: {logs['amount'].sum():,.2f}\n\n"
        "Breaks are expected in this synthetic set: they are deliberately planted\n"
        "so the pipeline has something to find, log and reconcile, as in a daily audit.\n"
        "See discrepancy_log.csv, reconciliation_report.csv and department_variance.csv.\n"
    )
    (OUT / "reconciliation_report.md").write_text(report)
    print(report)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
