# =============================================================================
# FILE PURPOSE:
# Real-world showcase demonstrating ingestion of semi-structured JSON records
# with optional or omitted fields across multiple document iterations.
# Eliminates verbose defensive chains (.get() or try/except) when parsing data.
# Run with regular python: `python3 examples/02_semi_structured_json.py`
# Run with SoftLookup-PVM: `softlookup-python examples/02_semi_structured_json.py`
# =============================================================================

"""
=============================================================================
DUAL RUN EXECUTION GUIDE
=============================================================================

🔴 1. RUNNING WITH REGULAR / UNMODIFIED PYTHON:
-----------------------------------------------------------------------------
Command:
    python3 examples/02_semi_structured_json.py

Expected Output / Failure:
    Traceback (most recent call last):
      File "examples/02_semi_structured_json.py", line 55, in process_order
        discount = order["coupon"]["code"]
    KeyError: 'coupon'

Explanation:
    When ingesting inhomogeneous document payloads, missing nested keys
    halt pipeline processing with KeyError unless every step is defensively
    guarded with `.get("coupon", {})` or nested `try/except` statements.


🟢 2. RUNNING WITH SOFTLOOKUP-PVM RUNTIME:
-----------------------------------------------------------------------------
Command:
    softlookup-python examples/02_semi_structured_json.py

Expected Output:
    [Processing Order 1001]
      Buyer: Alice
      Item: Mechanical Keyboard
      Coupon: SUMMER25
      Special Instructions: None (omitted in payload)
    [Processing Order 1002]
      Buyer: Bob
      Item: Gaming Mouse
      Coupon: None (omitted in payload)
      Special Instructions: Leave on front porch
    Telemetry Recorded: {'soft_key_misses': 3, 'soft_attr_misses': 0}
    Processed 2 orders cleanly in 0.0002s!

Explanation:
    SoftLookup-PVM resolves missing keys to None directly at the bytecode level,
    enabling expressive and concise data transformation pipelines.
=============================================================================
"""

import sys
import time

def process_orders():
    # Inhomogeneous JSON documents from an external API
    raw_orders = [
        {
            "order_id": "ORD-1001",
            "buyer": {"name": "Alice", "country": "US"},
            "item": "Mechanical Keyboard",
            "coupon": {"code": "SUMMER25", "discount": 0.25},
            # "notes" is omitted
        },
        {
            "order_id": "ORD-1002",
            "buyer": {"name": "Bob", "country": "DE"},
            "item": "Gaming Mouse",
            # "coupon" is completely omitted
            "notes": "Leave on front porch",
        }
    ]

    if hasattr(sys, "set_soft_lookup"):
        sys.set_soft_lookup(True)
        sys.reset_soft_lookup_stats()

    start_time = time.perf_counter()

    for order in raw_orders:
        order_id = order["order_id"]
        buyer_name = order["buyer"]["name"]
        item = order["item"]
        
        # Missing field access directly using clean subscription
        # In standard Python, this raises KeyError on ORD-1002!
        coupon = order["coupon"]
        coupon_code = coupon["code"] if coupon is not None else None
        notes = order["notes"]

        print(f"\n[Processing Order {order_id}]")
        print(f"  Buyer   : {buyer_name}")
        print(f"  Item    : {item}")
        print(f"  Coupon  : {coupon_code}")
        print(f"  Notes   : {notes}")

    elapsed = time.perf_counter() - start_time

    if hasattr(sys, "get_soft_lookup_stats"):
        print(f"\nTelemetry Recorded : {sys.get_soft_lookup_stats()}")
    print(f"Successfully processed {len(raw_orders)} orders in {elapsed:.6f}s!")

if __name__ == "__main__":
    process_orders()
