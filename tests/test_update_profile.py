from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "update_profile.py"
SPEC = importlib.util.spec_from_file_location("update_profile", MODULE_PATH)
assert SPEC and SPEC.loader
UPDATE_PROFILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPDATE_PROFILE)


class UpdateProfileTest(unittest.TestCase):
    def test_recent_oss_contributions_include_open_and_merged_prs(self) -> None:
        items = [
            {
                "repository_url": "https://api.github.com/repos/grafana/k8s-monitoring-helm",
                "number": 3090,
                "html_url": "https://github.com/grafana/k8s-monitoring-helm/pull/3090",
                "title": "align Helm tooling",
                "state": "open",
                "pull_request": {"merged_at": None},
            },
            {
                "repository_url": "https://api.github.com/repos/robusta-dev/krr",
                "number": 554,
                "html_url": "https://github.com/robusta-dev/krr/pull/554",
                "title": "fix AMP history",
                "state": "closed",
                "pull_request": {"merged_at": "2026-10-09T00:00:00Z"},
            },
            {
                "repository_url": "https://api.github.com/repos/robusta-dev/krr",
                "number": 553,
                "html_url": "https://github.com/robusta-dev/krr/pull/553",
                "title": "unmerged change",
                "state": "closed",
                "pull_request": {"merged_at": None},
            },
        ]
        with patch.object(UPDATE_PROFILE, "github_get", return_value={"items": items}) as get:
            output = UPDATE_PROFILE.render_oss_contributions("Iro-engin", 3, None)

        self.assertIn("is%3Apr", get.call_args.args[0])
        self.assertNotIn("is%3Amerged", get.call_args.args[0])
        self.assertIn("align Helm tooling (open PR)", output)
        self.assertIn("fix AMP history (merged PR)", output)
        self.assertNotIn("unmerged change", output)

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
