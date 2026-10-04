from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "update_profile.py"
SPEC = importlib.util.spec_from_file_location("update_profile", MODULE_PATH)
assert SPEC and SPEC.loader
UPDATE_PROFILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPDATE_PROFILE)


class UpdateProfileTest(unittest.TestCase):
    def test_normalize_description_collapses_whitespace(self) -> None:
        self.assertEqual(
            UPDATE_PROFILE.normalize_description("A  useful\n project"),
            "A useful project",
        )

    def test_replace_section_updates_only_named_section(self) -> None:
        document = (
            "Before\n<!-- demo:start -->\nold\n<!-- demo:end -->\nAfter\n"
        )
        self.assertEqual(
            UPDATE_PROFILE.replace_section(document, "demo", "new"),
            "Before\n<!-- demo:start -->\nnew\n<!-- demo:end -->\nAfter\n",
        )

    def test_replace_section_rejects_missing_marker(self) -> None:
        with self.assertRaises(ValueError):
            UPDATE_PROFILE.replace_section("No markers", "demo", "new")


if __name__ == "__main__":
    unittest.main()
