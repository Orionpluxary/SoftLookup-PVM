# =============================================================================
# FILE PURPOSE:
# Demonstrates scoped, temporary soft-lookup mode using the Pythonic
# `soft_lookup()` context manager from `src.runtime_client`.
# Confirms strict error handling before, soft handling during, and strictness after.
# Run with regular python: `python3 examples/03_context_manager.py` (or `wsl python3 ...`)
# Run with SoftLookup-PVM: `softlookup-python examples/03_context_manager.py` (or `wsl softlookup-python ...`)
# =============================================================================

"""
====================================================================================================
                                STEP-BY-STEP DUAL-RUN EXECUTION GUIDE
====================================================================================================

This guide provides the exact terminal commands and expected outputs for testing this script under
both Normal Python and your custom SoftLookup-PVM runtime.

----------------------------------------------------------------------------------------------------
🔴 TEST 1: RUNNING WITH REGULAR / UNMODIFIED PYTHON (Demonstrates Runtime Guard)
----------------------------------------------------------------------------------------------------

Where to run:
  • If your terminal is in Windows PowerShell:
        wsl python3 examples/03_context_manager.py
  • If your terminal is inside WSL / Ubuntu:
        python3 examples/03_context_manager.py

Exact Expected Terminal Output:
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Executing under: 3.14.4 (main, ...) [GCC ...] on linux                                           │
│                                                                                                  │
│ 1. Before Context: Testing Default Strict Behavior                                               │
│    [OK] Strict mode active: KeyError caught on record['extra'].                                  │
│                                                                                                  │
│ 2. Inside Context: Scoped Soft-Lookup Execution                                                  │
│ Traceback (most recent call last):                                                               │
│   File "examples/03_context_manager.py", line 75, in demo_context_manager                        │
│     with soft_lookup(auto_reset_stats=True):                                                     │
│   File "src/runtime_client.py", line 63, in soft_lookup                                          │
│     raise RuntimeError(                                                                          │
│ RuntimeError: Native Soft-Lookup Mode requires the SoftLookup-PVM runtime.                       │
│ Please run this code using /usr/local/bin/softlookup-python.                                     │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

Why it failed:
  The `src.runtime_client` library includes safety guards that check for native VM support
  and warn developers immediately if run under an unsupported Python interpreter.


----------------------------------------------------------------------------------------------------
🟢 TEST 2: RUNNING WITH SOFTLOOKUP-PVM (Demonstrates Scoped Context Success)
----------------------------------------------------------------------------------------------------

Where to run:
  • If your terminal is in Windows PowerShell:
        wsl softlookup-python examples/03_context_manager.py
  • If your terminal is inside WSL / Ubuntu:
        softlookup-python examples/03_context_manager.py

Exact Expected Terminal Output:
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Executing under: 3.16.0a2+dev (heads/main-dirty:a46c65c, ...) [GCC 15.2.0, SoftLookup-PVM]      │
│                                                                                                  │
│ 1. Before Context: Testing Default Strict Behavior                                               │
│    [OK] Strict mode active: KeyError caught on record['extra'].                                  │
│                                                                                                  │
│ 2. Inside Context: Scoped Soft-Lookup Execution                                                  │
│    record['extra'] resolved cleanly to: None                                                     │
│    Context telemetry: {'soft_key_misses': 1, 'soft_attr_misses': 0}                              │
│                                                                                                  │
│ 3. After Context: Verifying Strict Restoration                                                   │
│    [OK] Strict mode restored: KeyError caught on record['extra'].                                │
│                                                                                                  │
│ [SUCCESS] Context manager scoping and restoration verified!                                      │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

Why it succeeded:
  The context manager `with soft_lookup():` safely enables VM soft-lookup exclusively inside the
  context block and automatically restores strict CPython error behavior upon exiting.
====================================================================================================
"""

import sys
import os

# Ensure src can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.runtime_client import soft_lookup, get_stats, is_soft_lookup_supported

def demo_context_manager():
    print(f"Executing under: {sys.version}")

    record = {"primary_key": "PK_9910", "data": "payload_content"}

    print("\n1. Before Context: Testing Default Strict Behavior")
    try:
        _ = record["extra"]
        print("   [!] Unexpected: KeyError was not raised.")
    except KeyError:
        print("   [OK] Strict mode active: KeyError caught on record['extra'].")

    print("\n2. Inside Context: Scoped Soft-Lookup Execution")
    with soft_lookup(auto_reset_stats=True):
        extra_val = record["extra"]
        print(f"   record['extra'] resolved cleanly to: {extra_val}")
        stats = get_stats()
        print(f"   Context telemetry: {stats}")

    print("\n3. After Context: Verifying Strict Restoration")
    try:
        _ = record["extra"]
        print("   [!] Unexpected: KeyError was not raised after context exit.")
    except KeyError:
        print("   [OK] Strict mode restored: KeyError caught on record['extra'].")

    print("\n[SUCCESS] Context manager scoping and restoration verified!")

if __name__ == "__main__":
    demo_context_manager()
