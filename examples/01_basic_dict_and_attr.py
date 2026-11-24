# =============================================================================
# FILE PURPOSE:
# Introductory example demonstrating basic dictionary key and object attribute
# dereferencing under both standard Python and SoftLookup-PVM.
# Demonstrates missing keys and attributes returning None instead of crashing.
# Run with regular python: `python3 examples/01_basic_dict_and_attr.py`
# Run with SoftLookup-PVM: `softlookup-python examples/01_basic_dict_and_attr.py`
# =============================================================================

"""
=============================================================================
DUAL RUN EXECUTION GUIDE
=============================================================================

🔴 1. RUNNING WITH REGULAR / UNMODIFIED PYTHON:
-----------------------------------------------------------------------------
Command:
    python3 examples/01_basic_dict_and_attr.py

Expected Output / Failure:
    Traceback (most recent call last):
      File "examples/01_basic_dict_and_attr.py", line 45, in <module>
        nickname = user_dict["nickname"]
    KeyError: 'nickname'

Explanation:
    In standard unmodified Python, subscripting a dict with an absent key
    immediately raises a KeyError exception, halting the program unless
    wrapped in try/except or chained .get() calls.


🟢 2. RUNNING WITH SOFTLOOKUP-PVM RUNTIME:
-----------------------------------------------------------------------------
Command:
    softlookup-python examples/01_basic_dict_and_attr.py

Expected Output:
    [SoftLookup-PVM] Running on: 3.16.0a2+dev ... [GCC 15.2.0, SoftLookup-PVM]
    [Step 1] Enabling soft lookup mode via sys.set_soft_lookup(True)
    [Step 2] Accessing missing dictionary key 'nickname': None
    [Step 3] Accessing missing object attribute 'avatar_url': None
    [Step 4] Telemetry stats: {'soft_key_misses': 1, 'soft_attr_misses': 1}
    [Success] Execution completed without crashing!

Explanation:
    Under SoftLookup-PVM, the virtual machine intercepts KeyError and
    AttributeError at the VM level, returning None and recording telemetry.
=============================================================================
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

    # Check if native soft lookup is supported
    if hasattr(sys, "set_soft_lookup"):
        print("[SoftLookup-PVM Detected] Enabling soft-lookup mode...")
        sys.set_soft_lookup(True)
    else:
        print("[Standard Python Detected] Running in default strict mode...")

    print("\n--- Reading Dictionary Keys ---")
    print(f"user_dict['name']     (existing) -> {user_dict['name']}")
    nickname = user_dict["nickname"]  # In standard Python, raises KeyError here!
    print(f"user_dict['nickname'] (missing)  -> {nickname}")

    print("\n--- Reading Object Attributes ---")
    print(f"profile.bio           (existing) -> {profile.bio}")
    avatar = profile.avatar_url       # In standard Python, raises AttributeError here!
    print(f"profile.avatar_url    (missing)  -> {avatar}")

    if hasattr(sys, "get_soft_lookup_stats"):
        print(f"\n--- Telemetry ---")
        print(f"Telemetry: {sys.get_soft_lookup_stats()}")

    print("\n[SUCCESS] Completed all lookups!")

if __name__ == "__main__":
    main()
