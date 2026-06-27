import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crm import clv, data
from crm.rfm import customer_table, score_customers


def _scored(txns):
    rows = score_customers(customer_table(txns))
    return clv.add_clv(clv.churn_flags(rows))


def test_customer_table_aggregates():
    txns = [
        {"customer_id": "A", "invoice": "1", "date": "2024-01-01", "qty": 2, "price": 100, "country": "China"},
        {"customer_id": "A", "invoice": "2", "date": "2024-03-01", "qty": 1, "price": 50, "country": "China"},
        {"customer_id": "B", "invoice": "3", "date": "2024-02-01", "qty": 1, "price": 500, "country": "France"},
    ]
    rows = {r["customer_id"]: r for r in customer_table(txns, asof="2024-03-01")}
    assert rows["A"]["frequency"] == 2
    assert rows["A"]["monetary"] == 250.0
    assert rows["A"]["recency"] == 0          # last order is the asof date
    assert rows["B"]["recency"] == 29


def test_scores_in_range_and_segment():
    rows = _scored(data.generate_synthetic(n_customers=400, seed=2))
    for x in rows:
        assert 1 <= x["R"] <= 5 and 1 <= x["F"] <= 5 and 1 <= x["M"] <= 5
        assert x["segment"]
    assert any(x["segment"] == "Champions" for x in rows)


def test_champions_are_high_value():
    rows = _scored(data.generate_synthetic(n_customers=600, seed=4))
    champ = [x for x in rows if x["segment"] == "Champions"]
    others = [x for x in rows if x["segment"] == "Hibernating / Lost"]
    if champ and others:
        avg_c = sum(x["monetary"] for x in champ) / len(champ)
        avg_o = sum(x["monetary"] for x in others) / len(others)
        assert avg_c > avg_o


def test_revenue_concentration_pareto():
    rows = _scored(data.generate_synthetic(n_customers=800, seed=5))
    conc = clv.revenue_concentration(rows, 0.2)
    assert 0.0 < conc["rev_share"] <= 1.0
    assert conc["rev_share"] > 0.4            # luxury skew: top 20% > 40% of revenue


def test_clv_and_churn_present():
    rows = _scored(data.generate_synthetic(n_customers=300, seed=6))
    assert all(x["clv"] >= 0 for x in rows)
    assert all(x["churn_risk"] in ("low", "medium", "high") for x in rows)


def test_segment_summary_shares_sum_to_one():
    rows = _scored(data.generate_synthetic(n_customers=500, seed=7))
    segs = clv.segment_summary(rows)
    assert abs(sum(s["rev_share"] for s in segs) - 1.0) < 1e-2


def test_real_loader_cleans(tmp_path):
    p = tmp_path / "r.csv"
    p.write_text(
        "InvoiceNo,StockCode,Quantity,InvoiceDate,UnitPrice,CustomerID,Country\n"
        "536365,85123A,6,2024-01-01 08:26,2.55,17850,United Kingdom\n"   # good
        "C536379,D,-1,2024-01-01 09:41,27.5,14527,United Kingdom\n"      # cancellation
        "536400,22000,3,2024-01-02 10:00,1.5,,United Kingdom\n",         # no CustomerID
        encoding="utf-8",
    )
    txns = data.load_online_retail(str(p))
    assert len(txns) == 1
    assert txns[0]["customer_id"] == "17850"
