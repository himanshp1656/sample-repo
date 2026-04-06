from __future__ import annotations
from service import UserService
from orders import create_order, get_order_summary, cancel_order
from analytics import track_metric, get_metric_stats
from pipeline import run_pipeline
from errors import safe_call


def start_app():
    service = UserService()
    result = service.handle_request(101)
    print("User:", result)
    bulk = service.bulk_load([101, 202, 303])
    print("Bulk:", bulk)
    print("Stats:", service.stats())


def demo_orders():
    items = [
        {"product_id": 1, "quantity": 2, "unit_price": 9.99},
        {"product_id": 3, "quantity": 1, "unit_price": 49.99},
    ]
    order = create_order(user_id=42, items=items, discount_pct=10.0)
    print("Order created:", order.id, "Total:", order.net_total())
    summary = get_order_summary(user_id=42)
    print("Summary:", summary)
    cancelled = safe_call(cancel_order, order.id)
    print("Cancelled:", cancelled)


def demo_pipeline():
    records = [
        {"id": 1, "Name": "  Alice  ", "Score": 95},
        {"id": 2, "Name": "BOB",       "Score": 82},
        {"id": 2, "Name": "Bob dup",   "Score": 80},  # duplicate
        {"id": 3, "Name": "",          "Score": 71},
    ]
    results = run_pipeline(
        records,
        field_map={"Name": "name", "Score": "score"},
        dedup_key="id",
    )
    print("Pipeline output:", results)


def demo_analytics():
    for v in [12, 45, 33, 78, 91, 22, 55, 67, 44, 38]:
        track_metric("latency_ms", float(v))
    stats = get_metric_stats("latency_ms")
    print("Analytics:", stats)


if __name__ == "__main__":
    start_app()
    demo_orders()
    demo_pipeline()
    demo_analytics()
