"""Regression tests for persistent-memory trust levels.

The M15 notebook exposed an inverted comparison: ``recall(min_trust="user")``
returned values learned from documents and tool output. Trust levels are ordered
most-trusted first, so a caller must reject lower-trust entries, not higher-trust
ones.
"""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1] / "projects" / "ai-agents"
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from agent_core import PersistentMemory  # noqa: E402


class PersistentMemoryTrustTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.memory = PersistentMemory(Path(self._tmp.name) / "memory.json")
        self.memory.remember("preference", "window seat", source="user", trust="user")
        self.memory.remember("tool_note", "tool output", source="tool", trust="tool")
        self.memory.remember("policy", "30 days", source="page", trust="document")
        self.memory.remember("guess", "maybe", source="model", trust="model")

    def test_user_bar_excludes_lower_trust(self):
        self.assertEqual(self.memory.recall("preference", min_trust="user"), "window seat")
        self.assertIsNone(self.memory.recall("tool_note", min_trust="user"))
        self.assertIsNone(self.memory.recall("policy", min_trust="user"))
        self.assertIsNone(self.memory.recall("guess", min_trust="user"))

    def test_lower_bars_still_accept_higher_trust(self):
        self.assertEqual(self.memory.recall("preference", min_trust="document"), "window seat")
        self.assertEqual(self.memory.recall("policy", min_trust="document"), "30 days")
        self.assertIsNone(self.memory.recall("guess", min_trust="document"))

    def test_search_applies_the_same_bar(self):
        keys = {entry.key for entry in self.memory.search("window seat", min_trust="user")}
        self.assertEqual(keys, {"preference"})
        keys = {entry.key for entry in self.memory.search("window seat", min_trust="model")}
        self.assertIn("preference", keys)

    def test_purge_removes_every_non_user_entry(self):
        self.assertEqual(len(self.memory.untrusted()), 3)
        self.assertEqual(self.memory.forget_untrusted(), 3)
        self.assertEqual(self.memory.recall("preference"), "window seat")
        self.assertEqual(self.memory.untrusted(), [])


if __name__ == "__main__":
    unittest.main()
