"""RFM (Recency / Frequency / Monetary) per customer + quintile scoring + segments.

RFM + a named-segment map is the workhorse of luxury clienteling: it tells a client
advisor *who to call* — VIPs to nurture, high-value clients quietly lapsing to win back,
one-timers to convert.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date


def _parse(d: str) -> date | None:
    try:
        y, m, dd = d[:10].split("-")
        return date(int(y), int(m), int(dd))
    except Exception:
        return None


def customer_table(txns: list[dict], asof: str | None = None) -> list[dict]:
    """Aggregate transactions → one row per customer with recency/frequency/monetary."""
    dates = [dt for dt in (_parse(t["date"]) for t in txns) if dt]
    if not dates:
        return []
    ref = _parse(asof) if asof else max(dates)
    agg = defaultdict(lambda: {"orders": set(), "spend": 0.0, "units": 0,
                               "last": None, "first": None, "country": ""})
    for t in txns:
        dt = _parse(t["date"])
        if not dt:
            continue
        a = agg[t["customer_id"]]
        a["orders"].add(t["invoice"])
        a["spend"] += t["qty"] * t["price"]
        a["units"] += int(t["qty"])
        a["last"] = dt if a["last"] is None else max(a["last"], dt)
        a["first"] = dt if a["first"] is None else min(a["first"], dt)
        a["country"] = t.get("country", "") or a["country"]
    rows = []
    for cid, a in agg.items():
        freq = len(a["orders"])
        monetary = round(a["spend"], 2)
        rows.append({
            "customer_id": cid,
            "recency": (ref - a["last"]).days,
            "frequency": freq,
            "monetary": monetary,
            "avg_order_value": round(monetary / freq, 2) if freq else 0.0,
            "tenure_days": (a["last"] - a["first"]).days,
            "country": a["country"],
        })
    return rows


def _quintile_scores(values: list[float], reverse: bool = False) -> dict:
    """Map each value to 1..5 by quintile. reverse=True → low value scores high (recency)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    n = len(values)
    score = [0] * n
    for rank, idx in enumerate(order):
        q = min(4, rank * 5 // n)          # 0..4
        score[idx] = (5 - q) if reverse else (q + 1)
    return score


# segment map keyed on (R high/low, F high/low, M high/low) heuristics
def _segment(r: int, f: int, m: int) -> str:
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and m >= 4:
        return "Loyal / VIP"
    if r >= 4 and f <= 2:
        return "New / Promising"
    if r >= 3 and f >= 3:
        return "Potential Loyalist"
    if r <= 2 and f >= 4 and m >= 4:
        return "Can't Lose Them"       # high-value, lapsing → priority win-back
    if r <= 2 and m >= 3:
        return "At Risk"
    if r <= 2 and f <= 2:
        return "Hibernating / Lost"
    return "Needs Attention"


def score_customers(rows: list[dict]) -> list[dict]:
    """Attach R/F/M 1-5 scores and a named segment to each customer row."""
    if not rows:
        return rows
    rec = _quintile_scores([x["recency"] for x in rows], reverse=True)
    frq = _quintile_scores([x["frequency"] for x in rows])
    mon = _quintile_scores([x["monetary"] for x in rows])
    out = []
    for i, x in enumerate(rows):
        R, F, M = rec[i], frq[i], mon[i]
        out.append({**x, "R": R, "F": F, "M": M,
                    "rfm": f"{R}{F}{M}", "segment": _segment(R, F, M)})
    return out
