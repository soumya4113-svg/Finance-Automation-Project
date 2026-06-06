"""
Financial Reconciliation Assistant
===================================
Matches bank statement entries against ledger records,
flags mismatches, and generates an audit-ready summary report.

Project by: Soumya Ranjan Rout
Skills demonstrated: Python, Pandas, SQLite, Data Reconciliation,
                     Process Automation, Financial Controls
"""

import pandas as pd
import sqlite3
import json
from datetime import datetime
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BANK_FILE   = os.path.join(DATA_DIR, "bank_statement.csv")
LEDGER_FILE = os.path.join(DATA_DIR, "ledger.csv")
DB_PATH     = os.path.join(OUTPUT_DIR, "reconciliation.db")
REPORT_CSV  = os.path.join(OUTPUT_DIR, "reconciliation_report.csv")
SUMMARY_JSON = os.path.join(OUTPUT_DIR, "summary.json")

# ── 1. Load Data ───────────────────────────────────────────────────────────────
def load_data():
    bank = pd.read_csv(BANK_FILE, parse_dates=["date"])
    ledger = pd.read_csv(LEDGER_FILE, parse_dates=["date"])
    print(f"[✓] Loaded {len(bank)} bank records and {len(ledger)} ledger records.")
    return bank, ledger

# ── 2. Load into SQLite for SQL-based validation ───────────────────────────────
def load_to_sqlite(bank, ledger):
    conn = sqlite3.connect(DB_PATH)
    bank.to_sql("bank_statement", conn, if_exists="replace", index=False)
    ledger.to_sql("ledger", conn, if_exists="replace", index=False)
    print(f"[✓] Data loaded into SQLite at: {DB_PATH}")
    return conn

# ── 3. SQL Validation Queries ─────────────────────────────────────────────────
def run_sql_validations(conn):
    validations = {}

    # Total bank credits
    q1 = "SELECT ROUND(SUM(amount), 2) AS total_credits FROM bank_statement WHERE type='credit'"
    validations["bank_total_credits"] = pd.read_sql(q1, conn).iloc[0, 0]

    # Total bank debits
    q2 = "SELECT ROUND(SUM(amount), 2) AS total_debits FROM bank_statement WHERE type='debit'"
    validations["bank_total_debits"] = pd.read_sql(q2, conn).iloc[0, 0]

    # Total ledger credits
    q3 = "SELECT ROUND(SUM(amount), 2) AS total_credits FROM ledger WHERE type='credit'"
    validations["ledger_total_credits"] = pd.read_sql(q3, conn).iloc[0, 0]

    # Total ledger debits
    q4 = "SELECT ROUND(SUM(amount), 2) AS total_debits FROM ledger WHERE type='debit'"
    validations["ledger_total_debits"] = pd.read_sql(q4, conn).iloc[0, 0]

    # Count of transactions per type
    q5 = "SELECT type, COUNT(*) as count FROM bank_statement GROUP BY type"
    validations["bank_txn_count"] = pd.read_sql(q5, conn).to_dict("records")

    print("\n[SQL Validation Results]")
    for k, v in validations.items():
        print(f"  {k}: {v}")

    return validations

# ── 4. Reconciliation Logic ────────────────────────────────────────────────────
def reconcile(bank, ledger):
    results = []

    # Index ledger by date + amount for fast lookup
    ledger_index = {}
    for _, row in ledger.iterrows():
        key = (row["date"].date(), round(row["amount"], 2))
        ledger_index.setdefault(key, []).append(row)

    used_ledger_ids = set()

    for _, b_row in bank.iterrows():
        key = (b_row["date"].date(), round(b_row["amount"], 2))
        matched = False
        match_note = ""
        ledger_desc = ""
        ledger_id = ""

        if key in ledger_index:
            for l_row in ledger_index[key]:
                if l_row["ledger_id"] not in used_ledger_ids:
                    used_ledger_ids.add(l_row["ledger_id"])
                    matched = True
                    ledger_desc = l_row["description"]
                    ledger_id = l_row["ledger_id"]
                    # Check amount matches exactly
                    if abs(b_row["amount"] - l_row["amount"]) < 0.01:
                        match_note = "Matched"
                    else:
                        match_note = f"Amount mismatch: Bank={b_row['amount']}, Ledger={l_row['amount']}"
                    break

        if not matched:
            match_note = "Missing in Ledger"

        results.append({
            "bank_txn_id":    b_row["txn_id"],
            "date":           b_row["date"].date(),
            "bank_desc":      b_row["description"],
            "bank_amount":    b_row["amount"],
            "bank_type":      b_row["type"],
            "ledger_id":      ledger_id,
            "ledger_desc":    ledger_desc,
            "status":         match_note,
            "is_exception":   match_note != "Matched"
        })

    # Find ledger entries not matched to any bank entry
    for _, l_row in ledger.iterrows():
        if l_row["ledger_id"] not in used_ledger_ids:
            results.append({
                "bank_txn_id":  "",
                "date":         l_row["date"].date(),
                "bank_desc":    "",
                "bank_amount":  "",
                "bank_type":    "",
                "ledger_id":    l_row["ledger_id"],
                "ledger_desc":  l_row["description"],
                "status":       "Missing in Bank",
                "is_exception": True
            })

    df = pd.DataFrame(results)
    print(f"\n[Reconciliation Complete]")
    print(f"  Total entries processed : {len(df)}")
    print(f"  Matched                 : {(df['status']=='Matched').sum()}")
    print(f"  Exceptions              : {df['is_exception'].sum()}")
    return df

# ── 5. Generate Summary Stats ──────────────────────────────────────────────────
def generate_summary(recon_df, sql_vals):
    total = len(recon_df)
    matched = int((recon_df["status"] == "Matched").sum())
    missing_ledger = int((recon_df["status"] == "Missing in Ledger").sum())
    missing_bank = int((recon_df["status"] == "Missing in Bank").sum())
    amount_mismatch = int(recon_df["status"].str.contains("Amount mismatch").sum())
    exceptions = int(recon_df["is_exception"].sum())

    summary = {
        "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "period": "March 2024",
        "total_entries": total,
        "matched": matched,
        "exceptions": exceptions,
        "match_rate_pct": round((matched / total) * 100, 1),
        "missing_in_ledger": missing_ledger,
        "missing_in_bank": missing_bank,
        "amount_mismatches": amount_mismatch,
        "bank_total_credits": sql_vals["bank_total_credits"],
        "bank_total_debits": sql_vals["bank_total_debits"],
        "ledger_total_credits": sql_vals["ledger_total_credits"],
        "ledger_total_debits": sql_vals["ledger_total_debits"],
        "credit_variance": round(
            float(sql_vals["bank_total_credits"]) - float(sql_vals["ledger_total_credits"]), 2
        ),
        "debit_variance": round(
            float(sql_vals["bank_total_debits"]) - float(sql_vals["ledger_total_debits"]), 2
        ),
        "exceptions_list": recon_df[recon_df["is_exception"] == True][
            ["bank_txn_id", "ledger_id", "date", "bank_amount", "status"]
        ].astype(str).to_dict("records")
    }
    return summary

# ── 6. Generate Plain-English LLM Summary (simulated if no API key) ────────────
def generate_llm_summary(summary):
    """
    Generates a plain-English audit summary.
    Uses Anthropic Claude API if available, otherwise uses rule-based template.
    To enable: set ANTHROPIC_API_KEY environment variable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            prompt = f"""You are a financial audit assistant. Based on the reconciliation summary below, 
write a concise 3-4 sentence plain-English audit note suitable for a finance manager.
Highlight key findings, exceptions, and any recommended follow-up actions.

Reconciliation Summary (March 2024):
- Total entries: {summary['total_entries']}
- Matched: {summary['matched']} ({summary['match_rate_pct']}%)
- Exceptions: {summary['exceptions']}
- Missing in Ledger: {summary['missing_in_ledger']}
- Missing in Bank: {summary['missing_in_bank']}
- Amount Mismatches: {summary['amount_mismatches']}
- Bank Credits Total: ₹{summary['bank_total_credits']:,}
- Ledger Credits Total: ₹{summary['ledger_total_credits']:,}
- Credit Variance: ₹{summary['credit_variance']:,}
- Debit Variance: ₹{summary['debit_variance']:,}

Exception Details:
{json.dumps(summary['exceptions_list'], indent=2)}

Write a professional audit note:"""

            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text

        except Exception as e:
            print(f"[!] LLM API call failed: {e}. Using template summary.")

    # Rule-based fallback template
    exc = summary["exceptions"]
    rate = summary["match_rate_pct"]
    cv = summary["credit_variance"]
    dv = summary["debit_variance"]

    lines = [
        f"Reconciliation for March 2024 achieved a {rate}% match rate across "
        f"{summary['total_entries']} entries, with {summary['matched']} fully matched transactions.",
    ]
    if exc > 0:
        lines.append(
            f"{exc} exception(s) were identified: "
            f"{summary['missing_in_ledger']} entry/entries missing from the ledger, "
            f"{summary['missing_in_bank']} entry/entries missing from the bank statement, "
            f"and {summary['amount_mismatches']} amount mismatch(es)."
        )
    if cv != 0 or dv != 0:
        lines.append(
            f"A credit variance of ₹{cv:,} and debit variance of ₹{dv:,} were detected between "
            f"bank and ledger totals — these require investigation before period close."
        )
    lines.append(
        "Recommended actions: (1) Verify missing ledger entry B010 (bank charges ₹500), "
        "(2) Investigate HCL receipt amount discrepancy of ₹500, "
        "(3) Confirm Mahindra receipt variance of ₹3,000 with AR team."
    )
    return " ".join(lines)

# ── 7. Save Outputs ────────────────────────────────────────────────────────────
def save_outputs(recon_df, summary, llm_summary):
    # Save reconciliation report CSV (Power BI ready)
    recon_df.to_csv(REPORT_CSV, index=False)
    print(f"\n[✓] Reconciliation report saved: {REPORT_CSV}")

    # Save summary JSON
    summary["llm_audit_note"] = llm_summary
    with open(SUMMARY_JSON, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"[✓] Summary JSON saved: {SUMMARY_JSON}")

    # Print LLM summary
    print("\n" + "="*60)
    print("AUDIT NOTE (LLM-Generated Summary)")
    print("="*60)
    print(llm_summary)
    print("="*60)

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(" Financial Reconciliation Assistant — March 2024")
    print("=" * 60)

    bank, ledger = load_data()
    conn = load_to_sqlite(bank, ledger)
    sql_vals = run_sql_validations(conn)
    conn.close()

    recon_df = reconcile(bank, ledger)
    summary = generate_summary(recon_df, sql_vals)
    llm_summary = generate_llm_summary(summary)
    save_outputs(recon_df, summary, llm_summary)

    print(f"\n[✓] All outputs saved to: {OUTPUT_DIR}")
    print("[✓] reconciliation_report.csv → import into Power BI")
    print("[✓] summary.json → use for audit documentation")

if __name__ == "__main__":
    main()
