#!/usr/bin/env python3
"""luxe-clientele CLI — RFM segmentation, CLV & churn for luxury clienteling.

    python3 segment_clients.py                                 # synthetic demo
    python3 segment_clients.py --real data/online_retail.xlsx  # real UCI Online Retail
    python3 segment_clients.py --margin 0.65 --horizon 3
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm import clv, data, report
from crm.rfm import customer_table, score_customers


def main():
    ap = argparse.ArgumentParser(description="Luxury client segmentation (RFM + CLV)")
    ap.add_argument("--real", metavar="PATH", help="UCI Online Retail .xlsx/.csv")
    ap.add_argument("--margin", type=float, default=0.6, help="gross margin for CLV")
    ap.add_argument("--horizon", type=float, default=3.0, help="CLV horizon (years)")
    ap.add_argument("--asof", help="reference date YYYY-MM-DD (default: latest in data)")
    ap.add_argument("--out", default="out/clienteling_brief.md")
    args = ap.parse_args()

    if args.real:
        txns = data.load_online_retail(args.real)
        src = f"{args.real} ({len(txns):,} clean transactions)"
    else:
        txns = data.generate_synthetic()
        src = f"synthetic demo ({len(txns):,} transactions)"

    rows = customer_table(txns, asof=args.asof)
    rows = score_customers(rows)
    rows = clv.add_clv(rows, margin=args.margin, horizon_years=args.horizon)
    rows = clv.churn_flags(rows)

    md = report.build(rows)
    print(f"Source: {src}\n")
    print(md)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"<!-- source: {src} -->\n\n" + md)
    print(f"\n[written to {args.out}]")


if __name__ == "__main__":
    main()
