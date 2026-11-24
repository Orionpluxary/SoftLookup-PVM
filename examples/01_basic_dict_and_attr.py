# =============================================================================
# FILE PURPOSE:
# Introductory example demonstrating basic dictionary key and object attribute
# dereferencing under both standard Python and SoftLookup-PVM.
# Demonstrates missing keys and attributes returning None instead of crashing.
# Run with regular python: `python3 examples/01_basic_dict_and_attr.py` (or `wsl python3 ...`)
# Run with SoftLookup-PVM: `softlookup-python examples/01_basic_dict_and_attr.py` (or `wsl softlookup-python ...`)
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
        wsl python3 examples/01_basic_dict_and_attr.py
  • If your terminal is inside WSL / Ubuntu:
        python3 examples/01_basic_dict_and_attr.py

Exact Expected Terminal Output:
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Runtime Version: 3.14.4 (main, ... ) [GCC ...] on linux                                          │
│ [Standard Python Detected] Running in default strict mode...                                     │
│                                                                                                  │
│ --- Reading Dictionary Keys ---                                                                  │
│ user_dict['name']     (existing) -> Jane Doe                                                     │
│ Traceback (most recent call last):                                                               │
│   File "examples/01_basic_dict_and_attr.py", line 75, in main                                    │
│     nickname = user_dict["nickname"]                                                             │
│ KeyError: 'nickname'                                                                             │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

Why it failed:
  In standard Python, `user_dict["nickname"]` immediately allocates and raises a `KeyError`
  exception because the key does not exist. The script terminates prematurely at line 75.


----------------------------------------------------------------------------------------------------
🟢 TEST 2: RUNNING WITH SOFTLOOKUP-PVM (Demonstrates Successful Execution)
----------------------------------------------------------------------------------------------------

Where to run:
  • If your terminal is in Windows PowerShell:
        wsl softlookup-python examples/01_basic_dict_and_attr.py
  • If your terminal is inside WSL / Ubuntu:
        softlookup-python examples/01_basic_dict_and_attr.py

Exact Expected Terminal Output:
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Runtime Version: 3.16.0a2+dev (heads/main-dirty:a46c65c, ...) [GCC 15.2.0, SoftLookup-PVM]      │
│ [SoftLookup-PVM Detected] Enabling soft-lookup mode...                                           │
│                                                                                                  │
│ --- Reading Dictionary Keys ---                                                                  │
│ user_dict['name']     (existing) -> Jane Doe                                                     │
│ user_dict['nickname'] (missing)  -> None                                                         │
│                                                                                                  │
│ --- Reading Object Attributes ---                                                                │
│ profile.bio           (existing) -> Open source contributor                                      │
│ profile.avatar_url    (missing)  -> None                                                         │
│                                                                                                  │
│ --- Telemetry ---                                                                                │
│ Telemetry: {'soft_key_misses': 1, 'soft_attr_misses': 1}                                         │
│                                                                                                  │
│ [SUCCESS] Completed all lookups!                                                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

Why it succeeded:
  Under SoftLookup-PVM, `user_dict["nickname"]` and `profile.avatar_url` are intercepted directly
  inside CPython's VM layer. Instead of raising `KeyError` and `AttributeError`, the runtime
  increments atomic telemetry counters and returns `None` with balanced reference counts.
====================================================================================================
"""

import sys

def main():
    print(f"Runtime Version: {sys.version}")

    user_dict = {
        "id": 101,
        "name": "Jane Doe",
        "email": "jane@example.com"
        # 'nickname' is omitted
    }

    class UserProfile:
        def __init__(self, bio):
            self.bio = bio
            # 'avatar_url' is omitted

    profile = UserProfile("Open source contributor")

    # Step 1: Detect runtime and enable soft lookup if supported
    if hasattr(sys, "set_soft_lookup"):
        print("[SoftLookup-PVM Detected] Enabling soft-lookup mode...")
        sys.set_soft_lookup(True)
    else:
        print("[Standard Python Detected] Running in default strict mode...")

    # Step 2: Read dictionary keys (existing vs missing)
    print("\n--- Reading Dictionary Keys ---")
    print(f"user_dict['name']     (existing) -> {user_dict['name']}")
    nickname = user_dict["nickname"]  # In standard Python, raises KeyError here!
    print(f"user_dict['nickname'] (missing)  -> {nickname}")

    # Step 3: Read object attributes (existing vs missing)
    print("\n--- Reading Object Attributes ---")
    print(f"profile.bio           (existing) -> {profile.bio}")
    avatar = profile.avatar_url       # In standard Python, raises AttributeError here!
    print(f"profile.avatar_url    (missing)  -> {avatar}")

    # Step 4: Inspect telemetry statistics
    if hasattr(sys, "get_soft_lookup_stats"):
        print(f"\n--- Telemetry ---")
        print(f"Telemetry: {sys.get_soft_lookup_stats()}")

    print("\n[SUCCESS] Completed all lookups!")

if __name__ == "__main__":
    main()
