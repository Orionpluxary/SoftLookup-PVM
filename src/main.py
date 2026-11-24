# =============================================================================
# FILE PURPOSE:
# Main entry point and central architectural map for the SoftLookup-PVM repository.
# Displays the full codebase structure, verifies the active Python execution
# environment, and executes an interactive end-to-end quick-start demonstration.
# Run directly with: `softlookup-python src/main.py`
# =============================================================================

"""
=================================================================================
                          SOFTLOOKUP-PVM REPOSITORY MAP
=================================================================================

.
├── COMPARISON.md               <- Comprehensive visual before/after architectural diffs
├── README.md                   <- Publication-grade documentation, benchmarks, & guides
├── .gitignore                  <- Standard repository ignore rules
│
├── src/                        <- Core VM C headers, state implementations & client SDK
│   ├── main.py                 <- Central entry point & repository overview (This File)
│   ├── pycore_softlookup.h     <- Internal CPython VM declarations for soft lookup APIs
│   ├── softlookup.c            <- C implementation of atomic counters & VM state logic
│   └── runtime_client.py       <- Pythonic context managers (`with soft_lookup():`) & stats
│
├── scripts/                    <- Build, automated patch, and installation toolchain
│   ├── apply_patch.py          <- Automated source patcher for clean CPython trees
│   ├── build.sh                <- Full compilation script (configure, make -j, tarball SDK)
│   └── install.sh              <- Portable installer extracting runtime to /opt/softlookup-pvm
│
├── tests/                      <- Comprehensive test suite for verification
│   └── test_softlookup.py      <- Regression, ref-counting, telemetry, & strict-mode tests
│
└── examples/                   <- Runnable showcases with dual-run instructions
    ├── 01_basic_dict_and_attr.py <- Basic dict key and object attribute dereferencing
    ├── 02_semi_structured_json.py<- Ingesting sparse and incomplete JSON payload models
    └── 03_context_manager.py     <- Scoped context-manager usage & telemetry isolation

=================================================================================
"""

import sys
import os

# Add parent directory to path so 'src' can be imported cleanly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.runtime_client import soft_lookup, is_soft_lookup_supported, get_stats, reset_stats

def run_quickstart_demo():
    print("=" * 70)
    print("        SOFTLOOKUP-PVM: RUNTIME QUICK-START DEMO")
    print("=" * 70)
    print(f"Runtime Executable : {sys.executable}")
    print(f"Runtime Version    : {sys.version}")
    print(f"Native Supported   : {is_soft_lookup_supported()}")
    print("-" * 70)

    if not is_soft_lookup_supported():
        print("🔴 WARNING: Running under standard, unmodified Python runtime.")
        print("   Native VM soft-lookup is not supported in this interpreter.")
        print("   Run this script with: softlookup-python src/main.py\n")
        return

    print("🟢 Running under SoftLookup-PVM runtime.")
    
    # Sample semi-structured data
    user_record = {
        "id": "usr_4021",
        "username": "sarah_k",
        # missing: "tier", "billing_address", "quota"
    }

    class ServiceConfig:
        host = "10.0.1.15"
        port = 8080
        # missing: "timeout_ms", "ssl_cert", "max_conns"

    config = ServiceConfig()

    print("\n1. Standard Strict Mode Verification:")
    try:
        _ = user_record["tier"]
        print("   [!] Unexpected: missing key did not raise error.")
    except KeyError as e:
        print(f"   [OK] Default strict mode raised KeyError as expected: {e}")

    try:
        _ = config.timeout_ms
        print("   [!] Unexpected: missing attr did not raise error.")
    except AttributeError as e:
        print(f"   [OK] Default strict mode raised AttributeError as expected: {e}")

    print("\n2. Scoped Soft-Lookup Context Execution:")
    with soft_lookup(auto_reset_stats=True):
        print("   Entering `with soft_lookup():` block...")
        tier = user_record["tier"]
        addr = user_record["billing_address"]
        timeout = config.timeout_ms
        ssl_cert = config.ssl_cert

        print(f"   user_record['tier']            -> {tier} (type: {type(tier).__name__})")
        print(f"   user_record['billing_address'] -> {addr} (type: {type(addr).__name__})")
        print(f"   config.timeout_ms              -> {timeout} (type: {type(timeout).__name__})")
        print(f"   config.ssl_cert                -> {ssl_cert} (type: {type(ssl_cert).__name__})")
        print(f"   Scoped Telemetry Stats         -> {get_stats()}")

    print("\n3. Post-Context Strictness Restoration:")
    try:
        _ = user_record["quota"]
    except KeyError:
        print("   [OK] Strict KeyError behavior restored after exiting context.")

    print("\n" + "=" * 70)
    print(" Quick-start demo completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    run_quickstart_demo()
