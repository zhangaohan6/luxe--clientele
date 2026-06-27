"""Markdown clienteling brief from the RFM / CLV / churn analysis."""
from __future__ import annotations

from . import clv


def build(rows: list[dict], top_n: int = 10) -> str:
    n = len(rows)
    conc = clv.revenue_concentration(rows, 0.2)
    segs = clv.segment_summary(rows)
    total_rev = sum(x["monetary"] for x in rows)

    L = [f"# Clienteling Brief — {n:,} clients\n"]
    L.append(f"- **Total tracked revenue:** ${total_rev:,.0f}")
    L.append(f"- **Top 20% of clients drive {conc['rev_share']*100:.1f}% of revenue** "
             f"({conc['n_top']:,} clients) — classic luxury Pareto skew")

    L.append("\n## Segments (by revenue)")
    L.append("| Segment | Clients | Revenue | Rev share | Avg CLV |")
    L.append("|---|--:|--:|--:|--:|")
    for s in segs:
        L.append(f"| {s['segment']} | {s['clients']:,} | ${s['revenue']:,.0f} | "
                 f"{s['rev_share']*100:.1f}% | ${s['avg_clv']:,.0f} |")

    # priority win-back: high-value but lapsing
    rescue = [x for x in rows if x["segment"] in ("Can't Lose Them", "At Risk")]
    rescue.sort(key=lambda x: x.get("clv", x["monetary"]), reverse=True)
    if rescue:
        rev_at_risk = sum(x["monetary"] for x in rescue)
        L.append(f"\n## ⚠️ Priority win-back ({len(rescue):,} clients · "
                 f"${rev_at_risk:,.0f} historic revenue at risk)")
        L.append("High-value clients lapsing vs their own cadence — call these first:")
        L.append("\n| Client | Segment | Recency (d) | Freq | Spend | CLV |")
        L.append("|---|---|--:|--:|--:|--:|")
        for x in rescue[:top_n]:
            L.append(f"| {x['customer_id']} | {x['segment']} | {x['recency']} | "
                     f"{x['frequency']} | ${x['monetary']:,.0f} | ${x.get('clv',0):,.0f} |")

    # top VIPs by CLV
    vips = sorted(rows, key=lambda x: x.get("clv", 0), reverse=True)[:top_n]
    L.append("\n## 💎 Top clients by predicted CLV")
    L.append("| Client | Segment | Spend | Orders | CLV |")
    L.append("|---|---|--:|--:|--:|")
    for x in vips:
        L.append(f"| {x['customer_id']} | {x['segment']} | ${x['monetary']:,.0f} | "
                 f"{x['frequency']} | ${x.get('clv',0):,.0f} |")

    return "\n".join(L) + "\n"
