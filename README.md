# Luxe Clientele — RFM Segmentation & CLV for Luxury Clienteling

A Python tool that turns **transaction-level client data** into a **clienteling action list**:
which clients are VIPs to nurture, which **high-value clients are quietly lapsing** and need a
win-back call, and where **lifetime value** is concentrated. This is the core analysis behind
a luxury maison's **CRM / clienteling / consumer-data** function (WeChat membership, boutique
client advisors, repeat-purchase programs) — made transparent and reproducible.

Built to pair a **computer-science background** with a luxury **CRM / clienteling** role
(target: LVMH-style consumer-data internships). Companion to
[`luxe-pulse`](https://github.com/zhangaohan6/luxe-pulse) (brand social/review NLP) — together
they cover the **voice side** (what people say) and the **client side** (who buys, and how to
keep them).

## What it computes

- **RFM** — Recency / Frequency / Monetary per client, scored into 1–5 quintiles.
- **Named segments** — Champions, Loyal / VIP, Potential Loyalist, New, At Risk,
  **Can't Lose Them** (high-value lapsing), Hibernating / Lost — a *who-to-call* map.
- **CLV** — a transparent lifetime-value estimate (annual value × margin × horizon ×
  retention inferred from cadence & recency), not a black box.
- **Churn risk** — flags clients whose recency far exceeds *their own* purchase cadence.
- **Revenue concentration** — the luxury Pareto check (what the top 20% of clients drive).

## Quick start

```bash
pip install pandas openpyxl          # core RFM/CLV is stdlib; pandas/openpyxl read the data
python3 segment_clients.py                                  # synthetic demo
python3 segment_clients.py --real data/online_retail.xlsx --margin 0.6 --horizon 3
streamlit run app.py                                        # interactive dashboard
```

## Validation on real data — 397,884 transactions

Validated on the **UCI Online Retail** dataset — **397,884 cleaned transactions across
4,338 real customers** (cancellations and missing-CustomerID rows dropped, as a CRM analyst
would). The transaction structure (client × order × line-item) is identical to a maison's CRM
export, so the same engine runs unchanged.

- **Top 20% of clients drive 74.6% of revenue** — the steep luxury Pareto skew, quantified.
- **Champions (970 clients) generate 65% of revenue** at an average predicted CLV of ~$9.5k.
- **A win-back list of 707 lapsing high-value clients holds ~$1.09M of historic revenue** —
  e.g. one client spent **$77k** then went silent for **325 days**: exactly the call a client
  advisor should make first.
- Top clients by CLV are surfaced for VIP nurture (the highest reaches ~$475k predicted CLV).

> A seeded **synthetic generator** ships too (luxury-skewed VIP tail), so
> `python3 segment_clients.py` runs with zero setup and the tests are deterministic. The
> 23 MB source workbook is **not** committed (`data/` is git-ignored).

## Layout
```
crm/
  data.py     # synthetic transactions + real loader (UCI Online Retail .xlsx/.csv)
  rfm.py      # RFM aggregation, quintile scoring, named segments
  clv.py      # CLV, churn risk, revenue concentration, segment roll-up
  report.py   # markdown clienteling brief
segment_clients.py  # CLI (--real, --margin, --horizon)
app.py              # Streamlit dashboard
tests/              # 7 unit tests (RFM, segments, CLV, churn, Pareto, real loader)
```

## Tests
```bash
python3 -m pytest -q
```

*Author: Aohan Zhang · MIT License*
