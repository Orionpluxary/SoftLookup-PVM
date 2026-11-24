# =============================================================================
# FILE PURPOSE:
# Automated unit and regression test suite for SoftLookup-PVM.
# Validates default strict behavior, opt-in soft-lookup resolution to None,
# telemetry counter accuracy, non-swallowing of real runtime exceptions,
# and scope restoration. Run with: `softlookup-python tests/test_softlookup.py`
# or `softlookup-python -m unittest tests/test_softlookup.py`.
# =============================================================================

import sys
import os
import unittest

# Ensure src can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.runtime_client import soft_lookup, is_soft_lookup_supported, get_stats, reset_stats

class TestSoftLookup(unittest.TestCase):

    def setUp(self):
        if hasattr(sys, "set_soft_lookup"):
            sys.set_soft_lookup(False)
            sys.reset_soft_lookup_stats()

    def tearDown(self):
        if hasattr(sys, "set_soft_lookup"):
            sys.set_soft_lookup(False)
            sys.reset_soft_lookup_stats()

    def test_runtime_environment(self):
        """Verify the test is executing under the SoftLookup-PVM runtime."""
        self.assertTrue(
            hasattr(sys, "set_soft_lookup"),
            "This test suite must be run with the SoftLookup-PVM interpreter (softlookup-python)."
        )
        self.assertFalse(sys.get_soft_lookup(), "Initial soft-lookup mode should be False.")
        self.assertEqual(sys.get_soft_lookup_stats(), {"soft_key_misses": 0, "soft_attr_misses": 0})

    def test_default_strict_behavior(self):
        """Verify default mode raises KeyError and AttributeError on missing lookups."""
        data = {"key_a": 100}
        class Sample:
            attr_a = "hello"
        obj = Sample()

        # Missing dict key must raise KeyError
        with self.assertRaises(KeyError):
            _ = data["missing_key"]

        # Missing attribute must raise AttributeError
        with self.assertRaises(AttributeError):
            _ = obj.missing_attr

        # Telemetry should remain 0
        self.assertEqual(sys.get_soft_lookup_stats(), {"soft_key_misses": 0, "soft_attr_misses": 0})

    def test_soft_lookup_dict_keys(self):
        """Verify missing dictionary keys resolve to None and record telemetry."""
        sys.set_soft_lookup(True)
        self.assertTrue(sys.get_soft_lookup())

        payload = {"user_id": 42, "role": "admin"}
        
        # Existing keys work normally
        self.assertEqual(payload["user_id"], 42)
        self.assertEqual(payload["role"], "admin")

        # Missing keys return None without exception
        self.assertIsNone(payload["email"])
        self.assertIsNone(payload["nickname"])
        self.assertIsNone(payload["preferences"])

        stats = sys.get_soft_lookup_stats()
        self.assertEqual(stats["soft_key_misses"], 3)
        self.assertEqual(stats["soft_attr_misses"], 0)

    def test_soft_lookup_object_attributes(self):
        """Verify missing object attributes resolve to None and record telemetry."""
        sys.set_soft_lookup(True)

        class Node:
            def __init__(self, name):
                self.name = name

        node = Node("worker-01")

        # Existing attribute
        self.assertEqual(node.name, "worker-01")

        # Missing attributes return None
        self.assertIsNone(node.ip_address)
        self.assertIsNone(node.region)
        self.assertIsNone(getattr(node, "cluster_id"))

        stats = sys.get_soft_lookup_stats()
        self.assertEqual(stats["soft_key_misses"], 0)
        self.assertEqual(stats["soft_attr_misses"], 3)

    def test_real_exceptions_not_swallowed(self):
        """Verify real non-lookup errors (TypeError, IndexError, custom errors) are NOT swallowed."""
        sys.set_soft_lookup(True)

        d = {"a": 1}

        # TypeError on unhashable dict key
        with self.assertRaises(TypeError):
            _ = d[{}]

        # IndexError on sequence bounds
        with self.assertRaises(IndexError):
            _ = [1, 2, 3][99]

        # Explicit exception inside a property
        class Faulty:
            @property
            def broken(self):
                raise ValueError("explicit property error")

        faulty = Faulty()
        with self.assertRaises(ValueError):
            _ = faulty.broken

    def test_toggling_and_stats_reset(self):
        """Verify dynamic toggling between modes and stat resets."""
        d = {"x": 1}

        # Enable
        sys.set_soft_lookup(True)
        self.assertIsNone(d["y"])
        self.assertEqual(sys.get_soft_lookup_stats()["soft_key_misses"], 1)

        # Reset stats
        sys.reset_soft_lookup_stats()
        self.assertEqual(sys.get_soft_lookup_stats(), {"soft_key_misses": 0, "soft_attr_misses": 0})

        # Disable
        sys.set_soft_lookup(False)
        with self.assertRaises(KeyError):
            _ = d["y"]

    def test_context_manager(self):
        """Verify the Pythonic soft_lookup() context manager."""
        d = {"active": True}

        # Outside context: strict
        with self.assertRaises(KeyError):
            _ = d["token"]

        # Inside context: soft lookup
        with soft_lookup(auto_reset_stats=True):
            self.assertIsNone(d["token"])
            self.assertEqual(get_stats()["soft_key_misses"], 1)

        # Exited context: strictness restored
        with self.assertRaises(KeyError):
            _ = d["token"]

if __name__ == "__main__":
    unittest.main()
