# KYC Analysis Dashboard (Streamlit)

Streamlit version of the provided KYC expiry HTML dashboard. It keeps the dark look, supports RM filtering, free-text search, KPIs, charts, and a sortable customer table.

## Quick start
1. Install deps (recommended inside a virtual env):
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   streamlit run app.py
   ```

## Data
- The app reads `data/dashboard_data.json` (sample of 60 rows is included so it runs immediately).
- To use your full dataset from the original HTML, extract it once:
  ```bash
  python scripts/extract_from_html.py /path/to/your/original_dashboard.html
  ```
  This writes the full JSON to `data/dashboard_data.json`. Restart the app afterward.

## Features
- **Relationship Manager filter** (All + the RM list from the original dashboard)
- **Search** across all columns
- **KPIs** for expiry buckets
- **Bar chart** for customers by expiry bucket
- **Stacked bar chart** for expiry bucket × risk rating
- **Sortable table** (click column headers)

## GitHub repo
GitHub CLI is not available on this machine. After confirming your remote access, create a repo named `KYC Analysis Dashboard` on GitHub and push this folder (or share credentials and I can wire it up in a follow-up).
