"""Streamlit dashboard for luxe-clientele.

Run:  streamlit run app.py     (needs: pip install streamlit pandas openpyxl)
"""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from crm import clv, data
from crm.rfm import customer_table, score_customers

st.set_page_config(page_title="Luxe Clientele", page_icon="💎", layout="wide")
st.title("💎 Luxe Clientele — RFM Segmentation & CLV for Clienteling")
st.caption("Who to call: VIPs to nurture · high-value clients lapsing to win back · CLV concentration")

with st.sidebar:
    st.header("Data")
    up = st.file_uploader("Transactions (.csv / .xlsx)", type=["csv", "xlsx"])
    margin = st.slider("Gross margin (CLV)", 0.3, 0.8, 0.6, 0.05)
    horizon = st.slider("CLV horizon (years)", 1.0, 5.0, 3.0, 0.5)

if up is not None:
    os.makedirs("out", exist_ok=True)
    suffix = ".xlsx" if up.name.lower().endswith("xlsx") else ".csv"
    tmp = os.path.join("out", "_up" + suffix)
    with open(tmp, "wb") as f:
        f.write(up.getvalue())
    txns = data.load_online_retail(tmp)
    st.sidebar.success(f"{len(txns):,} clean transactions")
else:
    txns = data.generate_synthetic()

rows = score_customers(customer_table(txns))
rows = clv.churn_flags(clv.add_clv(rows, margin=margin, horizon_years=horizon))
df = pd.DataFrame(rows)

conc = clv.revenue_concentration(rows, 0.2)
segs = pd.DataFrame(clv.segment_summary(rows))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Clients", f"{len(rows):,}")
c2.metric("Revenue", f"${df['monetary'].sum():,.0f}")
c3.metric("Top-20% rev share", f"{conc['rev_share']*100:.0f}%")
rescue = df[df["segment"].isin(["Can't Lose Them", "At Risk"])]
c4.metric("Win-back revenue at risk", f"${rescue['monetary'].sum():,.0f}")

t1, t2, t3 = st.tabs(["Segments", "Win-back list", "Top CLV clients"])

with t1:
    st.bar_chart(segs.set_index("segment")["revenue"])
    st.dataframe(segs, use_container_width=True)

with t2:
    cols = ["customer_id", "segment", "recency", "frequency", "monetary", "clv", "churn_risk"]
    st.dataframe(rescue.sort_values("clv", ascending=False)[cols].head(40),
                 use_container_width=True)

with t3:
    cols = ["customer_id", "segment", "monetary", "frequency", "annual_value", "clv"]
    st.dataframe(df.sort_values("clv", ascending=False)[cols].head(40),
                 use_container_width=True)
