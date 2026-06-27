"""Data layer: transaction records + a seeded synthetic generator + real loaders.

A transaction is a plain dict:
    {customer_id, invoice, date (YYYY-MM-DD), qty, price, country}

Real loader targets the **UCI Online Retail** dataset (transaction-level, with a real
CustomerID) — the structure is identical to a luxury maison's CRM / clienteling export
(client × order × line-item), so the same RFM / CLV / churn engine runs unchanged.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta


# ------------------------------------------------------------------- synthetic
def generate_synthetic(n_customers: int = 1500, seed: int = 11, months: int = 12) -> list[dict]:
    """Transactions with a realistic luxury skew: a small VIP tail drives most spend."""
    rng = random.Random(seed)
    start = date(2024, 1, 1)
    horizon = months * 30
    countries = ["China", "France", "UK", "USA", "Japan", "UAE", "Singapore"]
    txns: list[dict] = []
    inv = 1000
    for cid in range(1, n_customers + 1):
        # archetype: VIP (5%), loyal (20%), regular (45%), one-off (30%)
        roll = rng.random()
        if roll < 0.05:
            n_orders, aov, recency_bias = rng.randint(8, 25), rng.uniform(2000, 9000), 0.85
        elif roll < 0.25:
            n_orders, aov, recency_bias = rng.randint(4, 9), rng.uniform(800, 2500), 0.6
        elif roll < 0.70:
            n_orders, aov, recency_bias = rng.randint(2, 4), rng.uniform(300, 1200), 0.45
        else:
            n_orders, aov, recency_bias = 1, rng.uniform(150, 900), rng.random()
        country = rng.choices(countries, weights=[30, 15, 12, 18, 10, 8, 7])[0]
        for _ in range(n_orders):
            # recency_bias high → orders cluster toward the recent end of the window
            t = rng.random() ** (1.0 / (0.4 + recency_bias))
            day = int(t * (horizon - 1)) if recency_bias >= 0.5 else rng.randint(0, horizon - 1)
            d = start + timedelta(days=day)
            inv += 1
            value = max(50.0, rng.gauss(aov, aov * 0.3))
            qty = rng.randint(1, 4)
            txns.append({
                "customer_id": str(cid),
                "invoice": str(inv),
                "date": d.isoformat(),
                "qty": qty,
                "price": round(value / qty, 2),
                "country": country,
            })
    txns.sort(key=lambda r: r["date"])
    return txns


# --------------------------------------------------------------- real adapters
def _to_float(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def load_online_retail(path: str) -> list[dict]:
    """Load the UCI Online Retail dataset (.xlsx or .csv) into transaction records.

    Cleans the way a CRM analyst would: drop rows with no CustomerID, drop cancellations
    (InvoiceNo starting 'C') and non-positive quantity/price.
    """
    rows = _read_any(path)
    out: list[dict] = []
    for r in rows:
        cid = str(r.get("CustomerID", "") or "").strip()
        if not cid or cid.lower() in ("nan", "none"):
            continue
        cid = cid.split(".")[0]                       # 12345.0 -> 12345
        inv = str(r.get("InvoiceNo", "") or "").strip()
        if inv.upper().startswith("C"):               # cancellation
            continue
        qty = _to_float(r.get("Quantity"))
        price = _to_float(r.get("UnitPrice"))
        if qty <= 0 or price <= 0:
            continue
        d = str(r.get("InvoiceDate", "") or "")[:10]
        out.append({
            "customer_id": cid,
            "invoice": inv,
            "date": d,
            "qty": qty,
            "price": price,
            "country": str(r.get("Country", "") or "").strip(),
        })
    return out


def _read_any(path: str) -> list[dict]:
    if path.lower().endswith((".xlsx", ".xls")):
        import pandas as pd
        df = pd.read_excel(path)
        df.columns = [str(c).strip() for c in df.columns]
        return df.to_dict("records")
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        return list(csv.DictReader(f))
