# =============================================================================
# FILE PURPOSE:
# Real-world showcase demonstrating ingestion of semi-structured JSON records
# with optional or omitted fields across multiple document iterations.
# Eliminates verbose defensive chains (.get() or try/except) when parsing data.
# Run with regular python: `python3 examples/02_semi_structured_json.py` (or `wsl python3 ...`)
# Run with SoftLookup-PVM: `softlookup-python examples/02_semi_structured_json.py` (or `wsl softlookup-python ...`)
# =============================================================================

"""
====================================================================================================
                                STEP-BY-STEP DUAL-RUN EXECUTION GUIDE
====================================================================================================

This guide provides the exact terminal commands and expected outputs for testing this script under
both Normal Python and your custom SoftLookup-PVM runtime.

----------------------------------------------------------------------------------------------------
🔴 TEST 1: RUNNING WITH REGULAR / UNMODIFIED PYTHON (Demonstrates Strict Failure)
----------------------------------------------------------------------------------------------------

Where to run:
  • If your terminal is in Windows PowerShell:
        wsl python3 examples/02_semi_structured_json.py
  • If your terminal is inside WSL / Ubuntu:
        python3 examples/02_semi_structured_json.py

Exact Expected Terminal Output:
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Processing Order ORD-1001]                                                                      │
│   Buyer   : Alice                                                                                │
│   Item    : Mechanical Keyboard                                                                  │
│   Coupon  : SUMMER25                                                                             │
│   Notes   : None                                                                                 │
│                                                                                                  │
│ [Processing Order ORD-1002]                                                                      │
│   Buyer   : Bob                                                                                  │
│   Item    : Gaming Mouse                                                                         │
│ Traceback (most recent call last):                                                               │
│   File "examples/02_semi_structured_json.py", line 82, in process_orders                          │
│     coupon = order["coupon"]                                                                     │
│ KeyError: 'coupon'                                                                               │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

Why it failed:
  Order ORD-1002 does not have a "coupon" key. In standard Python, accessing `order["coupon"]`
  raises an unhandled `KeyError`, crashing the ingestion pipeline.


----------------------------------------------------------------------------------------------------
🟢 TEST 2: RUNNING WITH SOFTLOOKUP-PVM (Demonstrates Successful Execution)
----------------------------------------------------------------------------------------------------

Where to run:
  • If your terminal is in Windows PowerShell:
        wsl softlookup-python examples/02_semi_structured_json.py
  • If your terminal is inside WSL / Ubuntu:
        softlookup-python examples/02_semi_structured_json.py

Exact Expected Terminal Output:
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Processing Order ORD-1001]                                                                      │
│   Buyer   : Alice                                                                                │
│   Item    : Mechanical Keyboard                                                                  │
│   Coupon  : SUMMER25                                                                             │
│   Notes   : None                                                                                 │
│                                                                                                  │
│ [Processing Order ORD-1002]                                                                      │
│   Buyer   : Bob                                                                                  │
│   Item    : Gaming Mouse                                                                         │
│   Coupon  : None                                                                                 │
│   Notes   : Leave on front porch                                                                 │
│                                                                                                  │
│ Telemetry Recorded : {'soft_key_misses': 2, 'soft_attr_misses': 0}                                │
│ Successfully processed 2 orders in 0.000050s!                                                    │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

Why it succeeded:
  SoftLookup-PVM seamlessly evaluates missing optional fields (`order["coupon"]` and
  `order["notes"]`) to `None` without raising exceptions or allocating traceback objects,
  increasing ingestion speed and code readability.
====================================================================================================
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
