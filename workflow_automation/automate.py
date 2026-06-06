"""
Finance Workflow Automation — Monthly Expense Report Generator
==============================================================
Automates the end-to-end monthly expense reporting workflow:
  1. Ingests raw expense data (messy, inconsistent formatting)
  2. Cleans and validates the data
  3. Transforms into structured output
  4. Computes budget vs. actuals by department and category
  5. Flags pending approvals and policy breaches
  6. Generates a formatted HTML report for stakeholders
  7. Exports Power BI-ready CSV output
  8. Simulates the Power Automate trigger (scheduled automation)

Project by: Soumya Ranjan Rout
Skills: Python, Pandas, Data Cleaning, Process Automation,
        Power Platform (Power Automate simulation), Power BI output,
        Governance & Controls documentation
"""

import pandas as pd
import os
import json
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")
OUT_DIR   = os.path.join(BASE_DIR, "output")
os.makedirs(OUT_DIR, exist_ok=True)

RAW_FILE     = os.path.join(DATA_DIR, "raw_expenses.csv")
BUDGET_FILE  = os.path.join(DATA_DIR, "department_budgets.csv")
CLEAN_CSV    = os.path.join(OUT_DIR, "clean_expenses.csv")
SUMMARY_CSV  = os.path.join(OUT_DIR, "dept_summary.csv")
REPORT_HTML  = os.path.join(OUT_DIR, "expense_report.html")
AUDIT_LOG    = os.path.join(OUT_DIR, "audit_log.json")

PERIOD = "March 2024"

# ── Policy Rules (Governance Controls) ────────────────────────────────────────
POLICY = {
    "Travel":          15000,   # Max single travel expense
    "Entertainment":    5000,   # Max single entertainment expense
    "Meals":            2000,   # Max single meals expense
    "Hardware":        20000,
    "Software":        20000,
    "Training":        15000,
    "Advertising":     50000,
    "Office Supplies":  5000,
}

# ── Step 1: Simulate Power Automate Trigger ────────────────────────────────────
def simulate_power_automate_trigger():
    """
    In production: Power Automate monitors a SharePoint folder.
    When a new raw_expenses.csv is uploaded by the last day of the month,
    it triggers this Python script via Azure Function or Power Automate
    'Run a script' action in Power Automate Desktop.
    Here we simulate that trigger event.
    """
    trigger_event = {
        "trigger":    "Scheduled – Monthly (last working day)",
        "source":     "SharePoint / OneDrive folder",
        "file":       "raw_expenses.csv",
        "triggered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status":     "Triggered successfully"
    }
    print("[Power Automate Trigger]")
    print(f"  Event   : {trigger_event['trigger']}")
    print(f"  Source  : {trigger_event['source']}")
    print(f"  Time    : {trigger_event['triggered_at']}")
    return trigger_event

# ── Step 2: Ingest and Clean Data ─────────────────────────────────────────────
def clean_data(raw_path):
    df = pd.read_csv(raw_path)
    original_count = len(df)
    issues = []

    # Standardize text fields
    df["status"]   = df["status"].str.strip().str.title()
    df["currency"] = df["currency"].str.strip().str.upper()
    df["department"] = df["department"].str.strip().str.title()
    df["category"] = df["category"].str.strip().str.title()
    df["employee_name"] = df["employee_name"].str.strip().str.title()

    # Parse dates
    df["expense_date"] = pd.to_datetime(df["expense_date"], errors="coerce")
    bad_dates = df["expense_date"].isna().sum()
    if bad_dates > 0:
        issues.append(f"{bad_dates} rows had unparseable dates — set to NaT")

    # Validate amounts — must be positive numbers
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    bad_amounts = df["amount"].isna().sum()
    if bad_amounts > 0:
        issues.append(f"{bad_amounts} rows had invalid amounts — dropped")
        df = df.dropna(subset=["amount"])

    # Fill missing approver for Pending rows
    df["approver"] = df["approver"].fillna("Awaiting Approval")

    # Add derived columns
    df["month"] = df["expense_date"].dt.strftime("%B %Y")
    df["week"]  = df["expense_date"].dt.isocalendar().week.astype(str)

    # Policy breach flag
    df["policy_limit"]   = df["category"].map(POLICY).fillna(99999)
    df["policy_breach"]  = df["amount"] > df["policy_limit"]

    cleaned_count = len(df)
    print(f"\n[Step 2: Data Cleaning]")
    print(f"  Original rows : {original_count}")
    print(f"  Cleaned rows  : {cleaned_count}")
    if issues:
        for i in issues:
            print(f"  [!] {i}")
    else:
        print(f"  No data issues found.")
    return df, issues

# ── Step 3: Validate Data ──────────────────────────────────────────────────────
def validate_data(df):
    validation_results = {}

    # Check for duplicates
    dupes = df.duplicated(subset=["emp_id", "expense_date", "amount"]).sum()
    validation_results["duplicate_records"] = int(dupes)

    # Pending approvals
    pending = df[df["status"] == "Pending"]
    validation_results["pending_approvals"] = len(pending)
    validation_results["pending_details"] = pending[["emp_id", "employee_name", "department", "amount", "description"]].to_dict("records")

    # Policy breaches
    breaches = df[df["policy_breach"] == True]
    validation_results["policy_breaches"] = len(breaches)
    validation_results["breach_details"] = breaches[["emp_id", "employee_name", "category", "amount", "policy_limit"]].to_dict("records")

    print(f"\n[Step 3: Data Validation]")
    print(f"  Duplicate records  : {dupes}")
    print(f"  Pending approvals  : {len(pending)}")
    print(f"  Policy breaches    : {len(breaches)}")
    if len(breaches) > 0:
        for _, b in breaches.iterrows():
            print(f"    → {b['employee_name']} | {b['category']} | ₹{b['amount']:,.0f} (limit ₹{b['policy_limit']:,.0f})")
    return validation_results

# ── Step 4: Transform — Budget vs. Actuals ────────────────────────────────────
def compute_budget_vs_actuals(df, budget_path):
    budget_df = pd.read_csv(budget_path)

    approved = df[df["status"] == "Approved"]
    dept_actual = approved.groupby("department")["amount"].sum().reset_index()
    dept_actual.columns = ["department", "actual_spend"]

    merged = pd.merge(budget_df, dept_actual, on="department", how="left")
    merged["actual_spend"] = merged["actual_spend"].fillna(0)
    merged["variance"]     = merged["monthly_budget_inr"] - merged["actual_spend"]
    merged["utilization_pct"] = (merged["actual_spend"] / merged["monthly_budget_inr"] * 100).round(1)
    merged["status_flag"]  = merged["variance"].apply(
        lambda v: "Over Budget" if v < 0 else ("Near Limit" if v < 2000 else "Within Budget")
    )

    print(f"\n[Step 4: Budget vs. Actuals]")
    print(merged[["department", "monthly_budget_inr", "actual_spend", "variance", "utilization_pct", "status_flag"]].to_string(index=False))
    return merged

# ── Step 5: Category Breakdown ─────────────────────────────────────────────────
def compute_category_breakdown(df):
    approved = df[df["status"] == "Approved"]
    cat = approved.groupby("category").agg(
        total_amount=("amount", "sum"),
        count=("amount", "count"),
        avg_amount=("amount", "mean")
    ).reset_index().sort_values("total_amount", ascending=False)
    cat["avg_amount"] = cat["avg_amount"].round(2)
    return cat

# ── Step 6: Generate HTML Report ──────────────────────────────────────────────
def generate_html_report(df, budget_summary, cat_breakdown, validation, period):
    approved_df = df[df["status"] == "Approved"]
    pending_df  = df[df["status"] == "Pending"]
    total_spend = approved_df["amount"].sum()
    total_budget = budget_summary["monthly_budget_inr"].sum()

    def dept_row(r):
        color = {"Over Budget": "#fee2e2", "Near Limit": "#fef9c3", "Within Budget": "#dcfce7"}.get(r["status_flag"], "#fff")
        return f"""<tr style="background:{color}">
            <td>{r['department']}</td>
            <td>₹{r['monthly_budget_inr']:,.0f}</td>
            <td>₹{r['actual_spend']:,.0f}</td>
            <td>₹{r['variance']:,.0f}</td>
            <td>{r['utilization_pct']}%</td>
            <td><span style="font-weight:500">{r['status_flag']}</span></td>
        </tr>"""

    def expense_row(r):
        status_color = "#dcfce7" if r["status"] == "Approved" else "#fef9c3"
        breach_note = " ⚠️" if r["policy_breach"] else ""
        return f"""<tr>
            <td>{r['emp_id']}</td>
            <td>{r['employee_name']}</td>
            <td>{r['department']}</td>
            <td>{r['category']}</td>
            <td>{str(r['expense_date'])[:10]}</td>
            <td>₹{r['amount']:,.0f}{breach_note}</td>
            <td style="background:{status_color}; font-weight:500">{r['status']}</td>
            <td>{r['approver']}</td>
        </tr>"""

    dept_rows   = "\n".join(budget_summary.apply(dept_row, axis=1))
    exp_rows    = "\n".join(df.sort_values("expense_date").apply(expense_row, axis=1))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Expense Report — {period}</title>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 13px; color: #1f2937; margin: 0; padding: 24px; background: #f9fafb; }}
  .header {{ background: #1e3a5f; color: white; padding: 20px 24px; border-radius: 8px; margin-bottom: 20px; }}
  .header h1 {{ margin: 0; font-size: 20px; }}
  .header p {{ margin: 4px 0 0; font-size: 13px; opacity: 0.8; }}
  .cards {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .card {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 20px; flex: 1; min-width: 140px; }}
  .card .label {{ font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }}
  .card .value {{ font-size: 22px; font-weight: 600; color: #111827; margin-top: 4px; }}
  .card .sub {{ font-size: 11px; color: #6b7280; margin-top: 2px; }}
  .section {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px; }}
  .section h2 {{ font-size: 14px; font-weight: 600; margin: 0 0 12px; color: #1e3a5f; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th {{ background: #f3f4f6; text-align: left; padding: 8px 10px; font-weight: 600; color: #374151; }}
  td {{ padding: 7px 10px; border-bottom: 1px solid #f3f4f6; }}
  tr:last-child td {{ border-bottom: none; }}
  .alert {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 10px 14px; border-radius: 4px; margin-bottom: 8px; font-size: 12px; }}
  .footer {{ font-size: 11px; color: #9ca3af; margin-top: 20px; text-align: center; }}
</style>
</head>
<body>

<div class="header">
  <h1>Monthly Expense Report — {period}</h1>
  <p>Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')} &nbsp;|&nbsp; Automated via Python Workflow Automation &nbsp;|&nbsp; Prepared by: Finance Team</p>
</div>

<div class="cards">
  <div class="card">
    <div class="label">Total Approved Spend</div>
    <div class="value">₹{total_spend:,.0f}</div>
    <div class="sub">of ₹{total_budget:,.0f} budget</div>
  </div>
  <div class="card">
    <div class="label">Budget Utilization</div>
    <div class="value">{round(total_spend/total_budget*100, 1)}%</div>
    <div class="sub">Overall</div>
  </div>
  <div class="card">
    <div class="label">Total Expenses</div>
    <div class="value">{len(df)}</div>
    <div class="sub">{len(approved_df)} approved · {len(pending_df)} pending</div>
  </div>
  <div class="card">
    <div class="label">Pending Approvals</div>
    <div class="value" style="color:#d97706">{validation['pending_approvals']}</div>
    <div class="sub">Require action</div>
  </div>
  <div class="card">
    <div class="label">Policy Breaches</div>
    <div class="value" style="color:{'#dc2626' if validation['policy_breaches']>0 else '#16a34a'}">{validation['policy_breaches']}</div>
    <div class="sub">Flagged entries</div>
  </div>
</div>

{''.join([f'<div class="alert">⚠️ <strong>Pending Approval:</strong> {p["employee_name"]} ({p["department"]}) — ₹{p["amount"]:,.0f} for {p["description"]}</div>' for p in validation["pending_details"]])}

<div class="section">
  <h2>Department Budget vs. Actuals</h2>
  <table>
    <tr><th>Department</th><th>Budget (₹)</th><th>Actuals (₹)</th><th>Variance (₹)</th><th>Utilization</th><th>Status</th></tr>
    {dept_rows}
  </table>
</div>

<div class="section">
  <h2>All Expense Entries</h2>
  <table>
    <tr><th>Emp ID</th><th>Name</th><th>Department</th><th>Category</th><th>Date</th><th>Amount</th><th>Status</th><th>Approver</th></tr>
    {exp_rows}
  </table>
  <p style="font-size:11px; color:#6b7280; margin-top:8px;">⚠️ = Policy limit exceeded</p>
</div>

<div class="footer">
  This report was auto-generated by the Finance Workflow Automation System. Do not edit manually.<br>
  For queries: finance-ops@company.com &nbsp;|&nbsp; Audit trail: audit_log.json
</div>

</body>
</html>"""
    return html

# ── Step 7: Save All Outputs ───────────────────────────────────────────────────
def save_outputs(df, budget_summary, html_report, validation, trigger_event, issues):
    # Clean CSV (Power BI ready)
    df.to_csv(CLEAN_CSV, index=False)
    print(f"\n[✓] Clean expense CSV saved: {CLEAN_CSV}")

    # Department summary CSV
    budget_summary.to_csv(SUMMARY_CSV, index=False)
    print(f"[✓] Department summary CSV saved: {SUMMARY_CSV}")

    # HTML report
    with open(REPORT_HTML, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"[✓] HTML report saved: {REPORT_HTML}")

    # Audit log (governance documentation)
    audit = {
        "workflow_run": trigger_event,
        "data_issues":  issues,
        "validation":   {k: v for k, v in validation.items() if k not in ["pending_details", "breach_details"]},
        "pending_count": validation["pending_approvals"],
        "breach_count":  validation["policy_breaches"],
        "outputs_generated": [CLEAN_CSV, SUMMARY_CSV, REPORT_HTML],
        "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(AUDIT_LOG, "w") as f:
        json.dump(audit, f, indent=2)
    print(f"[✓] Audit log saved: {AUDIT_LOG}")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"  Finance Workflow Automation — {PERIOD}")
    print("=" * 60)

    trigger      = simulate_power_automate_trigger()
    df, issues   = clean_data(RAW_FILE)
    validation   = validate_data(df)
    budget_sum   = compute_budget_vs_actuals(df, BUDGET_FILE)
    cat_break    = compute_category_breakdown(df)
    html_report  = generate_html_report(df, budget_sum, cat_break, validation, PERIOD)
    save_outputs(df, budget_sum, html_report, validation, trigger, issues)

    print(f"\n{'='*60}")
    print(f"  Workflow complete. All outputs in: {OUT_DIR}")
    print(f"  → expense_report.html  : Share with management")
    print(f"  → clean_expenses.csv   : Import into Power BI")
    print(f"  → dept_summary.csv     : Budget dashboard data")
    print(f"  → audit_log.json       : Governance documentation")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
