"""Interactive fraud monitoring dashboard powered by Snowflake."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import streamlit as st

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

st.set_page_config(
    page_title="Bank Fraud Monitor",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Bank Fraud Monitoring")
st.caption("Snowflake-powered analytics | Synthetic demonstration data")

DB = "FRAUD_DEMO"
CORE_TABLE = f"{DB}.CORE.TRANSACTIONS"
DAILY_TABLE = f"{DB}.ANALYTICS.DT_DAILY_TRANSACTION_SUMMARY"
COUNTRY_TABLE = f"{DB}.ANALYTICS.DT_FRAUD_RISK_SUMMARY"
HIGH_RISK_VIEW = f"{DB}.ANALYTICS.V_HIGH_RISK_TRANSACTIONS"
KPI_VIEW = f"{DB}.ANALYTICS.V_FRAUD_DASHBOARD_KPIS"


@st.cache_resource
def get_connection() -> Any:
    """Create a reusable Snowflake connection from Streamlit secrets."""
    return st.connection("snowflake")


@st.cache_data(ttl=60, show_spinner="Loading dashboard metrics...")
def load_query(sql: str) -> pd.DataFrame:
    """Run a read-only analytics query and cache results for 60 seconds."""
    connection = get_connection()
    return connection.query(sql, ttl=60)


def safe_load_query(sql: str, label: str) -> pd.DataFrame:
    """Display a useful error if Snowflake query execution fails."""
    try:
        return load_query(sql)
    except Exception as exc:  # Log details for developers; show safe message to users.
        LOGGER.exception("Failed to load %s from Snowflake", label)
        st.error(
            f"Could not load {label}. Check your Snowflake connection, "
            "object permissions, and whether the SQL setup script completed."
        )
        with st.expander("Technical details"):
            st.code(str(exc))
        return pd.DataFrame()


with st.sidebar:
    st.header("Dashboard controls")
    st.write("Data source: `FRAUD_DEMO`")
    if st.button("Refresh dashboard", use_container_width=True):
        load_query.clear()
        st.rerun()
    st.caption("Results are cached for up to 60 seconds.")

kpi_df = safe_load_query(
    f"SELECT * FROM {KPI_VIEW}",
    "overall KPI metrics",
)
daily_df = safe_load_query(
    f"""
    SELECT TRANSACTION_DATE, COUNTRY, TRANSACTION_TYPE,
           TRANSACTION_COUNT, TOTAL_AMOUNT, AVG_AMOUNT,
           AVG_RISK_SCORE, UNIQUE_CUSTOMERS
    FROM {DAILY_TABLE}
    ORDER BY TRANSACTION_DATE
    """,
    "daily transaction summary",
)
country_df = safe_load_query(
    f"SELECT * FROM {COUNTRY_TABLE}",
    "country fraud summary",
)
risk_df = safe_load_query(
    f"""
    SELECT TRANSACTION_ID, TRANSACTION_TS, CUSTOMER_ID, ACCOUNT_ID,
           AMOUNT, CURRENCY, TRANSACTION_TYPE, MERCHANT_NAME, COUNTRY,
           IS_FRAUD, RISK_SCORE, TRANSACTION_STATUS, FRAUD_CLASSIFICATION
    FROM {HIGH_RISK_VIEW}
    ORDER BY RISK_SCORE DESC, TRANSACTION_TS DESC
    LIMIT 5000
    """,
    "high-risk transactions",
)

if kpi_df.empty:
    st.info(
        "No KPI data is available yet. Run the Snowflake SQL setup script, "
        "then confirm that FRAUD_DEMO.CORE.TRANSACTIONS contains records."
    )
    st.stop()

kpis = kpi_df.iloc[0].to_dict()


def number_value(key: str) -> float:
    """Return a numeric KPI safely, defaulting to zero when missing."""
    value = kpis.get(key, 0)
    return float(value) if pd.notna(value) else 0.0


total_transactions = number_value("TOTAL_TRANSACTIONS")
unique_customers = number_value("UNIQUE_CUSTOMERS")
total_amount = number_value("TOTAL_TRANSACTION_AMOUNT")
confirmed_fraud = number_value("CONFIRMED_FRAUD_COUNT")
suspicious = number_value("SUSPICIOUS_COUNT")
blocked = number_value("DECLINED_OR_BLOCKED_COUNT")
fraud_rate = number_value("CONFIRMED_FRAUD_RATE")
avg_risk = number_value("AVG_RISK_SCORE")

st.subheader("Executive overview")
metric_cols = st.columns(4)
metric_cols[0].metric("Transactions", f"{total_transactions:,.0f}")
metric_cols[1].metric("Transaction value", f"${total_amount:,.2f}")
metric_cols[2].metric("Confirmed fraud", f"{confirmed_fraud:,.0f}")
metric_cols[3].metric("Confirmed fraud rate", f"{fraud_rate:.1%}")

metric_cols_2 = st.columns(4)
metric_cols_2[0].metric("Unique customers", f"{unique_customers:,.0f}")
metric_cols_2[1].metric("Suspicious transactions", f"{suspicious:,.0f}")
metric_cols_2[2].metric("Declined / blocked", f"{blocked:,.0f}")
metric_cols_2[3].metric("Average risk score", f"{avg_risk:.2f}")

st.divider()

overview_tab, trends_tab, investigation_tab, data_tab = st.tabs(
    ["Overview", "Trends & geography", "Transaction investigation", "Data quality"]
)

with overview_tab:
    left, right = st.columns(2)

    with left:
        st.subheader("Transaction classifications")
        classification_df = safe_load_query(
            f"""
            SELECT FRAUD_CLASSIFICATION, COUNT(*) AS TRANSACTION_COUNT
            FROM {CORE_TABLE}
            GROUP BY FRAUD_CLASSIFICATION
            ORDER BY TRANSACTION_COUNT DESC
            """,
            "transaction classifications",
        )
        if not classification_df.empty:
            classification_df = classification_df.set_index("FRAUD_CLASSIFICATION")
            st.bar_chart(classification_df["TRANSACTION_COUNT"])
        else:
            st.info("No classification data available.")

    with right:
        st.subheader("Transaction status")
        status_df = safe_load_query(
            f"""
            SELECT TRANSACTION_STATUS, COUNT(*) AS TRANSACTION_COUNT
            FROM {CORE_TABLE}
            GROUP BY TRANSACTION_STATUS
            ORDER BY TRANSACTION_COUNT DESC
            """,
            "transaction status breakdown",
        )
        if not status_df.empty:
            status_df = status_df.set_index("TRANSACTION_STATUS")
            st.bar_chart(status_df["TRANSACTION_COUNT"])
        else:
            st.info("No transaction status data available.")

    st.subheader("Latest high-risk transactions")
    if not risk_df.empty:
        st.dataframe(risk_df.head(10), use_container_width=True, hide_index=True)
    else:
        st.info("No high-risk transactions found or the query returned no data.")

with trends_tab:
    st.subheader("Daily transaction volume")
    if not daily_df.empty:
        daily_df["TRANSACTION_DATE"] = pd.to_datetime(
            daily_df["TRANSACTION_DATE"], errors="coerce"
        )
        daily_volume = (
            daily_df.groupby("TRANSACTION_DATE", as_index=True)["TRANSACTION_COUNT"]
            .sum()
            .sort_index()
        )
        st.line_chart(daily_volume)

        st.subheader("Daily transaction value")
        daily_amount = (
            daily_df.groupby("TRANSACTION_DATE", as_index=True)["TOTAL_AMOUNT"]
            .sum()
            .sort_index()
        )
        st.line_chart(daily_amount)

        st.subheader("Country-level risk")
        if not country_df.empty:
            country_chart = country_df[
                ["COUNTRY", "CONFIRMED_FRAUD_COUNT", "SUSPICIOUS_COUNT"]
            ].copy()
            country_chart = country_chart.set_index("COUNTRY")
            st.bar_chart(country_chart)
            st.dataframe(country_df, use_container_width=True, hide_index=True)
        else:
            st.info("No country summary data available.")
    else:
        st.info(
            "No daily trend data is available. Check whether the dynamic table "
            "has completed its initial refresh."
        )

with investigation_tab:
    st.subheader("Search and filter high-risk transactions")

    if risk_df.empty:
        st.info("No high-risk transactions are available to filter.")
    else:
        filtered = risk_df.copy()
        filter_cols = st.columns(3)

        countries = sorted(
            filtered["COUNTRY"].dropna().astype(str).unique().tolist()
        )
        selected_countries = filter_cols[0].multiselect(
            "Country",
            options=countries,
            default=countries,
        )

        statuses = sorted(
            filtered["TRANSACTION_STATUS"].dropna().astype(str).unique().tolist()
        )
        selected_statuses = filter_cols[1].multiselect(
            "Transaction status",
            options=statuses,
            default=statuses,
        )

        classes = sorted(
            filtered["FRAUD_CLASSIFICATION"].dropna().astype(str).unique().tolist()
        )
        selected_classes = filter_cols[2].multiselect(
            "Fraud classification",
            options=classes,
            default=classes,
        )

        filtered["RISK_SCORE"] = pd.to_numeric(
            filtered["RISK_SCORE"], errors="coerce"
        )
        min_score = float(filtered["RISK_SCORE"].min()) if filtered["RISK_SCORE"].notna().any() else 0.0
        max_score = float(filtered["RISK_SCORE"].max()) if filtered["RISK_SCORE"].notna().any() else 1.0
        risk_range = st.slider(
            "Risk score range",
            min_value=0.0,
            max_value=1.0,
            value=(max(0.0, min_score), min(1.0, max_score)),
            step=0.01,
        )

        search_id = st.text_input("Transaction ID (optional)")
        filtered = filtered[
            filtered["COUNTRY"].astype(str).isin(selected_countries)
            & filtered["TRANSACTION_STATUS"].astype(str).isin(selected_statuses)
            & filtered["FRAUD_CLASSIFICATION"].astype(str).isin(selected_classes)
            & filtered["RISK_SCORE"].between(risk_range[0], risk_range[1])
        ]

        if search_id.strip():
            filtered = filtered[
                filtered["TRANSACTION_ID"].astype(str).str.contains(
                    search_id.strip(), case=False, na=False
                )
            ]

        st.caption(
            f"Showing {len(filtered):,} matching rows from the latest "
            f"{len(risk_df):,} high-risk records retrieved (maximum 5,000)."
        )
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        csv_data = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download filtered results as CSV",
            data=csv_data,
            file_name="high_risk_transactions.csv",
            mime="text/csv",
        )

with data_tab:
    st.subheader("Pipeline and data checks")
    check_cols = st.columns(3)
    check_cols[0].metric("Raw rows", "Query below")
    check_cols[1].metric("Core rows", f"{total_transactions:,.0f}")
    check_cols[2].metric("High-risk rows retrieved", f"{len(risk_df):,}")

    raw_count = safe_load_query(
        f"SELECT COUNT(*) AS ROW_COUNT FROM {DB}.RAW.TRANSACTIONS_RAW",
        "raw row count",
    )
    core_count = safe_load_query(
        f"SELECT COUNT(*) AS ROW_COUNT FROM {CORE_TABLE}",
        "core row count",
    )

    if not raw_count.empty and not core_count.empty:
        raw_rows = int(raw_count.iloc[0]["ROW_COUNT"])
        core_rows = int(core_count.iloc[0]["ROW_COUNT"])
        st.write(f"Raw rows: **{raw_rows:,}**")
        st.write(f"Core rows: **{core_rows:,}**")
        if raw_rows == core_rows:
            st.success("Raw and core row counts match.")
        else:
            st.warning(
                "Raw and core row counts differ. This may be expected if "
                "invalid rows were filtered or if the scheduled task has not "
                "processed all new rows yet."
            )

    st.caption(
        "This dashboard uses synthetic demo records. Counts and fraud rates "
        "are illustrative and must not be treated as production risk metrics."
    )
