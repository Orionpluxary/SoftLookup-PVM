# =============================================================================
# FILE PURPOSE:
# High-level Python client library and context managers for SoftLookup-PVM.
# This module provides the `soft_lookup()` context manager, telemetry snapshot
# helpers, and graceful fallbacks when executing under standard CPython runtimes.
# Run or import this module from your application code: `from src.runtime_client import soft_lookup`.
# =============================================================================

import sys
import contextlib
from typing import Dict, Any, Optional

# Check if runtime supports native soft lookup
HAS_NATIVE_SOFT_LOOKUP = hasattr(sys, "set_soft_lookup") and hasattr(sys, "get_soft_lookup")

def is_soft_lookup_supported() -> bool:
    """Return True if running on a SoftLookup-PVM custom runtime."""
    return HAS_NATIVE_SOFT_LOOKUP

def is_enabled() -> bool:
    """Return True if Soft-Lookup mode is currently active."""
    if HAS_NATIVE_SOFT_LOOKUP:
        return sys.get_soft_lookup()
    return False

def set_enabled(enabled: bool) -> None:
    """
    Enable or disable Soft-Lookup mode in the underlying runtime.
    
    ORIGINAL PYTHON EQUIVALENT:
    -------------------------------------------------------------------------
    In standard Python, there is no VM-level switch. Developers must write
    defensive wrapper classes or chained `.get()` calls for every access.
    
    SOFTLOOKUP-PVM UPGRADED BEHAVIOR:
    -------------------------------------------------------------------------
    Directly toggles the CPython interpreter VM lookup interceptor.
    """
    if HAS_NATIVE_SOFT_LOOKUP:
        sys.set_soft_lookup(bool(enabled))
    else:
        raise RuntimeError(
            "Native Soft-Lookup Mode requires SoftLookup-PVM runtime. "
            "Run this script with 'softlookup-python'."
        )

def get_stats() -> Dict[str, int]:
    """Retrieve soft-lookup telemetry counters (soft_key_misses, soft_attr_misses)."""
    if HAS_NATIVE_SOFT_LOOKUP:
        return sys.get_soft_lookup_stats()
    return {"soft_key_misses": 0, "soft_attr_misses": 0}

def reset_stats() -> None:
    """Reset soft-lookup telemetry counters back to zero."""
    if HAS_NATIVE_SOFT_LOOKUP:
        sys.reset_soft_lookup_stats()

@contextlib.contextmanager
def soft_lookup(auto_reset_stats: bool = False):
    """
    Context manager that temporarily enables Soft-Lookup mode for a block of code,
    restoring the prior mode upon exit.

    Example:
        with soft_lookup():
            val = record["missing_key"]  # Returns None, does not raise KeyError
            attr = obj.missing_attr       # Returns None, does not raise AttributeError
    """
    if not HAS_NATIVE_SOFT_LOOKUP:
        raise RuntimeError(
            "Native Soft-Lookup Mode requires the SoftLookup-PVM runtime.\n"
            "Please run this code using /usr/local/bin/softlookup-python."
        )

    previous_state = sys.get_soft_lookup()
    if auto_reset_stats:
        sys.reset_soft_lookup_stats()
    sys.set_soft_lookup(True)
    try:
        yield
    finally:
        sys.set_soft_lookup(previous_state)
