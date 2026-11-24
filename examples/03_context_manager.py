# =============================================================================
# FILE PURPOSE:
# Demonstrates scoped, temporary soft-lookup mode using the Pythonic
# `soft_lookup()` context manager from `src.runtime_client`.
# Confirms strict error handling before, soft handling during, and strictness after.
# Run with regular python: `python3 examples/03_context_manager.py`
# Run with SoftLookup-PVM: `softlookup-python examples/03_context_manager.py`
# =============================================================================

"""
=============================================================================
DUAL RUN EXECUTION GUIDE
=============================================================================

🔴 1. RUNNING WITH REGULAR / UNMODIFIED PYTHON:
-----------------------------------------------------------------------------
Command:
    python3 examples/03_context_manager.py

Expected Output / Failure:
    RuntimeError: Native Soft-Lookup Mode requires the SoftLookup-PVM runtime.
    Please run this code using /usr/local/bin/softlookup-python.

Explanation:
    The `soft_lookup()` context manager safely detects whether the host
    interpreter supports the underlying CPython VM soft-lookup subsystem,
    raising an informative error if run under an unsupported runtime.


🟢 2. RUNNING WITH SOFTLOOKUP-PVM RUNTIME:
-----------------------------------------------------------------------------
Command:
    softlookup-python examples/03_context_manager.py

Expected Output:
    [Before Context] Strict mode active: KeyError raised on record['extra']
    [Inside Context] Soft-lookup active: record['extra'] -> None
    [Inside Context] Telemetry captured: {'soft_key_misses': 1, 'soft_attr_misses': 0}
    [After Context]  Strict mode restored: KeyError raised on record['extra']
    Context manager demo completed successfully!

Explanation:
    `with soft_lookup():` provides RAII-style scoped isolation, ensuring that
    soft-lookup semantics are active only during designated data ingestion
    blocks and strictly deactivated elsewhere in production applications.
=============================================================================
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
