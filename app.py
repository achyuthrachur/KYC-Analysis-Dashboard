import json
from pathlib import Path
from typing import Tuple

import altair as alt
import pandas as pd
import streamlit as st


st.set_page_config(page_title="KYC Expiry Dashboard", layout="wide")

DATA_PATH = Path(__file__).parent / "data" / "dashboard_data.json"
BUCKET_ORDER = ["Expired", "0-30 days", "31-60 days", "61-90 days", "90+ days"]
RISK_ORDER = ["High", "Medium", "Low", "Unknown"]
BUCKET_COLORS = {
    "Expired": "#ef4444",
    "0-30 days": "#f59e0b",
    "31-60 days": "#fbbf24",
    "61-90 days": "#60a5fa",
    "90+ days": "#34d399",
}
RISK_COLORS = {
    "High": "#b91c1c",
    "Medium": "#d97706",
    "Low": "#15803d",
    "Unknown": "#475569",
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --bg: #0b1220; --panel: #0f172a; --text: #e5e7eb; --muted:#94a3b8;
          --accent:#22d3ee; --border:#1f2937;
        }
        .stApp { background: var(--bg); color: var(--text); }
        .block-container { padding-top: 1.5rem; }
        .metric-card {
          background: var(--panel); border:1px solid var(--border); border-radius: 12px; padding: 0.75rem 0.9rem;
        }
        .metric-label { color: var(--muted); font-size: 0.85rem; margin-bottom: 0.35rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_data(path: Path) -> Tuple[dict, pd.DataFrame]:
    if not path.exists():
        return {}, pd.DataFrame()
    raw = json.loads(path.read_text(encoding="utf-8"))
    df = pd.DataFrame(raw.get("records", []))
    if df.empty:
        return raw, df

    df["risk_rating"] = df["risk_rating"].fillna("Unknown")
    df["expiry_bucket"] = pd.Categorical(df["expiry_bucket"], categories=BUCKET_ORDER, ordered=True)
    df["risk_rating"] = pd.Categorical(df["risk_rating"], categories=RISK_ORDER, ordered=True)
    df["days_to_expiry"] = pd.to_numeric(df["days_to_expiry"], errors="coerce")
    df["doc_expiry_date"] = pd.to_datetime(df["doc_expiry_date"], errors="coerce")
    return raw, df


def filter_rows(df: pd.DataFrame, rm: str, query: str) -> pd.DataFrame:
    if df.empty:
        return df
    filtered = df
    if rm and rm != "All":
        filtered = filtered[filtered["relationship_manager"] == rm]
    if query:
        q = query.lower()
        mask = filtered.apply(lambda row: any(q in str(v).lower() for v in row.values), axis=1)
        filtered = filtered[mask]
    return filtered


def render_kpis(df: pd.DataFrame) -> pd.Series:
    counts = df["expiry_bucket"].value_counts().reindex(BUCKET_ORDER, fill_value=0)
    cols = st.columns(len(BUCKET_ORDER))
    labels = ["Expired", "0–30 days", "31–60 days", "61–90 days", "90+ days"]
    for col, bucket, label in zip(cols, BUCKET_ORDER, labels):
        with col:
            st.markdown(
                f"<div class='metric-card'><div class='metric-label'>{label}</div>"
                f"<div style='font-size:1.6rem;font-weight:700;color:{BUCKET_COLORS[bucket]};'>{counts[bucket]}</div></div>",
                unsafe_allow_html=True,
            )
    return counts


def chart_buckets(df: pd.DataFrame):
    counts = df["expiry_bucket"].value_counts().reindex(BUCKET_ORDER, fill_value=0).reset_index()
    counts.columns = ["expiry_bucket", "count"]
    chart = (
        alt.Chart(counts)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("expiry_bucket:N", sort=BUCKET_ORDER, title="Expiry bucket"),
            y=alt.Y("count:Q", title="Customers"),
            color=alt.Color(
                "expiry_bucket:N",
                scale=alt.Scale(domain=list(BUCKET_COLORS.keys()), range=list(BUCKET_COLORS.values())),
                legend=None,
            ),
            tooltip=["expiry_bucket", "count"],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def chart_stack(df: pd.DataFrame):
    idx = pd.MultiIndex.from_product([BUCKET_ORDER, RISK_ORDER], names=["expiry_bucket", "risk_rating"])
    grouped = (
        df.groupby(["expiry_bucket", "risk_rating"])
        .size()
        .reindex(idx, fill_value=0)
        .reset_index(name="count")
    )
    chart = (
        alt.Chart(grouped)
        .mark_bar()
        .encode(
            x=alt.X("expiry_bucket:N", sort=BUCKET_ORDER, title="Expiry bucket"),
            y=alt.Y("count:Q", title="Customers"),
            color=alt.Color(
                "risk_rating:N",
                sort=RISK_ORDER,
                scale=alt.Scale(domain=list(RISK_COLORS.keys()), range=list(RISK_COLORS.values())),
                legend=alt.Legend(title="Risk rating"),
            ),
            tooltip=["expiry_bucket", "risk_rating", "count"],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def render_table(df: pd.DataFrame):
    if df.empty:
        st.info("No customers match the current filters.")
        return
    display = df.copy()
    display["doc_expiry_date"] = display["doc_expiry_date"].dt.strftime("%Y-%m-%d")
    cols = [
        "customer_id",
        "customer_name",
        "risk_rating",
        "kyc_document_type",
        "doc_expiry_date",
        "days_to_expiry",
        "expiry_bucket",
        "relationship_manager",
    ]
    st.dataframe(
        display[cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "days_to_expiry": st.column_config.NumberColumn("Days", format="d"),
            "doc_expiry_date": st.column_config.DateColumn("Expiry Date"),
            "risk_rating": st.column_config.TextColumn("Risk"),
        },
    )


def main():
    inject_css()
    raw, df = load_data(DATA_PATH)

    st.title("KYC Expiry Dashboard")
    meta = []
    if raw.get("generated_at"):
        meta.append(f"Generated {raw['generated_at']}")
    if raw.get("input_file"):
        meta.append(f"Source: {raw['input_file']}")
    if meta:
        st.caption(" • ".join(meta))

    if df.empty:
        st.warning(
            "No data found. Drop your dashboard JSON in `data/dashboard_data.json` "
            "or run the extraction script to generate it from the provided HTML."
        )
        return

    rm_options = raw.get("tabs") or ["All"] + sorted(df["relationship_manager"].dropna().unique().tolist())
    if "All" not in rm_options:
        rm_options = ["All"] + rm_options

    top_cols = st.columns([2, 3])
    with top_cols[0]:
        rm_choice = st.selectbox("Relationship manager", options=rm_options, index=0)
    with top_cols[1]:
        search = st.text_input("Search customers, document type, RM…", placeholder="e.g. passport, Johnson, Aarav")

    filtered = filter_rows(df, rm_choice, search)

    st.markdown("### Key Performance Indicators")
    render_kpis(filtered)

    st.markdown("### Trends")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.subheader("Customers by expiry bucket", divider="blue")
        chart_buckets(filtered)
    with chart_cols[1]:
        st.subheader("Expiry bucket × risk rating", divider="blue")
        chart_stack(filtered)

    st.markdown("### Customer details")
    st.caption("Click column headers to sort; search box filters across all columns.")
    render_table(filtered)


if __name__ == "__main__":
    main()
