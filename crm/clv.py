"""Customer lifetime value (CLV) + churn risk + revenue concentration.

A transparent, defensible CLV (not a black box): expected annual value × gross margin ×
expected retained years, where retention is inferred from purchase cadence and recency.
"""
from __future__ import annotations


def add_clv(rows: list[dict], margin: float = 0.6, horizon_years: float = 3.0) -> list[dict]:
    """Attach predicted CLV to each scored customer row.

    annual_value  = monetary / max(tenure_years, observed window ~1y)
    retention     = f(recency vs cadence)  → 0.2..0.95
    clv           = annual_value * margin * horizon_years * retention
    """
    out = []
    for x in rows:
        years = max(x.get("tenure_days", 0) / 365.0, 1.0)
        annual = x["monetary"] / years
        cadence = (x.get("tenure_days", 0) / max(x["frequency"] - 1, 1)) or 180
        # lapsed relative to own cadence → retention decays
        overdue = x["recency"] / max(cadence, 30)
        retention = max(0.2, min(0.95, 0.95 - 0.25 * overdue))
        clv = annual * margin * horizon_years * retention
        out.append({**x, "annual_value": round(annual, 2),
                    "retention": round(retention, 2), "clv": round(clv, 2)})
    return out


def churn_flags(rows: list[dict]) -> list[dict]:
    """Flag clients whose recency far exceeds their own typical inter-purchase gap."""
    out = []
    for x in rows:
        cadence = (x.get("tenure_days", 0) / max(x["frequency"] - 1, 1)) if x["frequency"] > 1 else None
        if cadence and x["recency"] > 2.5 * cadence:
            risk = "high"
        elif cadence and x["recency"] > 1.5 * cadence:
            risk = "medium"
        else:
            risk = "low"
        out.append({**x, "churn_risk": risk})
    return out


def revenue_concentration(rows: list[dict], top_frac: float = 0.2) -> dict:
    """Pareto check: what share of revenue comes from the top `top_frac` of clients."""
    if not rows:
        return {"top_frac": top_frac, "rev_share": 0.0, "n_top": 0, "total": 0.0}
    s = sorted(rows, key=lambda x: x["monetary"], reverse=True)
    total = sum(x["monetary"] for x in s) or 1.0
    k = max(1, int(len(s) * top_frac))
    top_rev = sum(x["monetary"] for x in s[:k])
    return {"top_frac": top_frac, "rev_share": round(top_rev / total, 4),
            "n_top": k, "n_total": len(s), "total": round(total, 2)}


def segment_summary(rows: list[dict]) -> list[dict]:
    """Roll up by segment: client count, revenue, revenue share, avg CLV."""
    from collections import defaultdict
    agg = defaultdict(lambda: {"n": 0, "rev": 0.0, "clv": 0.0})
    total = sum(x["monetary"] for x in rows) or 1.0
    for x in rows:
        a = agg[x["segment"]]
        a["n"] += 1
        a["rev"] += x["monetary"]
        a["clv"] += x.get("clv", 0.0)
    out = []
    for seg, a in agg.items():
        out.append({"segment": seg, "clients": a["n"],
                    "revenue": round(a["rev"], 2),
                    "rev_share": round(a["rev"] / total, 4),
                    "avg_clv": round(a["clv"] / a["n"], 2) if a["n"] else 0.0})
    return sorted(out, key=lambda r: r["revenue"], reverse=True)
