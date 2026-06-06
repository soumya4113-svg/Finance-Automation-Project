# Finance Automation Projects
### AI-Powered Reconciliation & Workflow Automation

**Author:** Soumya Ranjan Rout  
**Stack:** Python · SQL · Power BI · LLM Integration · Power Automate  
**Domain:** Finance Automation · GenAI · Process Efficiency

---

## Overview

This repository contains two end-to-end finance automation projects that demonstrate the application of Python, SQL, Generative AI, and Microsoft Power Platform concepts to real-world finance and operational workflows.

Both projects are built to mirror enterprise-grade automation patterns used in financial institutions — covering data ingestion, validation, reconciliation, reporting, LLM-assisted summarization, and governance documentation.

---

## Projects

### Project 1 — AI-Powered Financial Reconciliation Assistant

> Automates bank statement vs. ledger reconciliation using Python, SQL, and LLM-generated audit summaries.

**Folder:** `reconciliation_project/`

#### What it does
- Loads bank statement and ledger data from CSV files
- Persists data into SQLite and runs SQL queries for financial validation (totals, variances, transaction counts)
- Applies rule-based matching logic to reconcile entries by date and amount
- Flags exceptions: missing entries, amount mismatches, unmatched ledger items
- Integrates an LLM (Anthropic Claude API) via prompt engineering to generate plain-English audit notes
- Falls back to a rule-based summary generator if no API key is configured
- Exports a Power BI-ready reconciliation report CSV and a structured JSON summary for audit documentation

#### Tech stack
| Tool | Usage |
|------|-------|
| Python (Pandas) | Data loading, matching logic, exception flagging |
| SQLite + SQL | Data persistence, validation queries, aggregations |
| Anthropic Claude API | LLM-generated audit note via prompt engineering |
| CSV / JSON | Power BI output and audit documentation |

#### Key outputs
```
output/
├── reconciliation_report.csv   ← Import into Power BI for dashboard
├── summary.json                ← Audit-ready documentation with LLM note
└── reconciliation.db           ← SQLite database for SQL-based validation
```

#### How to run
```bash
cd reconciliation_project
pip install pandas anthropic
python reconcile.py
```

To enable LLM summaries, set your API key before running:
```bash
export ANTHROPIC_API_KEY=your_key_here
python reconcile.py
```

#### Sample output (LLM audit note)
```
Reconciliation for March 2024 achieved a 70.6% match rate across 17 entries,
with 12 fully matched transactions. 5 exceptions were identified: 3 entries
missing from the ledger, 2 entries missing from the bank statement. A credit
variance of ₹2,500 requires investigation before period close. Recommended
actions: verify B010 bank charges entry, investigate HCL receipt discrepancy,
and confirm Mahindra receipt variance with the AR team.
```

---

### Project 2 — Finance Workflow Automation (Power Automate + Python)

> Automates the end-to-end monthly expense reporting workflow — from raw messy data to formatted stakeholder reports.

**Folder:** `workflow_automation/`

#### What it does
- Simulates a Power Automate scheduled trigger (monthly, last working day)
- Ingests raw expense data with inconsistent formatting (mixed case, missing values, irregular currencies)
- Cleans and standardizes data: normalizes text fields, parses dates, validates amounts
- Flags policy breaches based on configurable per-category spending limits
- Computes department-level budget vs. actuals with variance and utilization percentages
- Generates a formatted HTML expense report for distribution to stakeholders
- Exports a clean CSV for Power BI dashboard integration
- Produces a structured audit log for governance and compliance documentation

#### Tech stack
| Tool | Usage |
|------|-------|
| Python (Pandas) | Data cleaning, validation, transformation |
| Power Automate | Scheduled trigger simulation (production: Azure Function / PA Desktop) |
| HTML/CSS | Stakeholder-ready formatted expense report |
| CSV / JSON | Power BI output and audit log |

#### Key outputs
```
output/
├── expense_report.html     ← Formatted report for stakeholders / email attachment
├── clean_expenses.csv      ← Power BI-ready clean data
├── dept_summary.csv        ← Budget vs. actuals by department
└── audit_log.json          ← Governance documentation and workflow run log
```

#### How to run
```bash
cd workflow_automation
pip install pandas
python automate.py
```

#### Governance controls documented
- Duplicate record detection
- Pending approval flagging with employee details
- Per-category policy limit enforcement
- Full audit trail in `audit_log.json` (trigger event, data issues, validation results, output file list, timestamp)

---

## Project Structure

```
finance-automation-projects/
│
├── README.md
│
├── reconciliation_project/
│   ├── reconcile.py
│   ├── data/
│   │   ├── bank_statement.csv
│   │   └── ledger.csv
│   └── output/
│       ├── reconciliation_report.csv
│       ├── summary.json
│       └── reconciliation.db
│
└── workflow_automation/
    ├── automate.py
    ├── data/
    │   ├── raw_expenses.csv
    │   └── department_budgets.csv
    └── output/
        ├── expense_report.html
        ├── clean_expenses.csv
        ├── dept_summary.csv
        └── audit_log.json
```

---

## Skills Demonstrated

- **Python automation** — data ingestion, cleaning, transformation, reporting
- **SQL** — SQLite queries for validation, aggregation, and data integrity checks
- **LLM integration** — prompt engineering with Anthropic Claude API for workflow enhancement
- **Power Platform concepts** — Power Automate trigger simulation, Power BI-ready outputs
- **Financial domain knowledge** — reconciliation logic, budget vs. actuals, expense policy controls
- **Governance & compliance** — audit logs, control documentation, structured exception reporting
- **End-to-end solution design** — from raw data ingestion to stakeholder-ready output

---

## About

These projects were built to demonstrate practical application of AI and automation within finance and operational workflows — aligned with GenAI & automation roles at financial institutions.

**Connect:** [LinkedIn](https://www.linkedin.com/in/soumya-ranjan-rout) | **Location:** Bhubaneswar, Odisha  
**Background:** BBA Finance & Accounting, Utkal University | Power BI · Excel · SQL · Python
