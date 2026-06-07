"""Tests for scripts/verify/docs_index_unknown_routes.py."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "verify" / "docs_index_unknown_routes.py"

spec = importlib.util.spec_from_file_location("docs_index_unknown_routes", SCRIPT)
docs_index_unknown_routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs_index_unknown_routes)


class DocsIndexUnknownRoutesTests(unittest.TestCase):
    def _docs_index(self, entries: list[dict[str, str]]) -> dict[str, object]:
        return {
            "artifact": "docs-index.json",
            "artifact_schema_version": "1.2.0",
            "scope": {"surface": "test", "excludes": []},
            "pages": [
                {
                    "path": entry["page"],
                    "route_classification_source": entry.get("source", "unknown"),
                    "related_route_entries": [
                        {
                            "route": entry["route"],
                            "route_type": entry.get("route_type", "unknown"),
                            "route_classification_reason": entry.get(
                                "reason", "metadata_not_provided"
                            ),
                        }
                    ],
                }
                for entry in entries
            ],
        }

    def test_unknown_route_report_is_sorted_and_counts_reasons(self):
        docs_index = self._docs_index(
            [
                {
                    "page": "b.md",
                    "route": "GET /b",
                    "reason": "crossref_route_missing",
                },
                {"page": "a.md", "route": "GET /a", "reason": "metadata_not_provided"},
                {
                    "page": "known.md",
                    "route": "GET /known",
                    "route_type": "canonical",
                    "source": "metadata",
                    "reason": "metadata_explicit",
                },
            ]
        )

        report = docs_index_unknown_routes.build_unknown_routes_report(docs_index)

        self.assertIn(
            "reason_counts: {crossref_route_missing: 1, metadata_not_provided: 1}", report
        )
        self.assertLess(
            report.index("crossref_route_missing"), report.index("metadata_not_provided")
        )
        self.assertIn("b.md | GET /b | unknown | unknown | crossref_route_missing", report)
        self.assertIn("a.md | GET /a | unknown | unknown | metadata_not_provided", report)
        self.assertNotIn("known.md", report)

    def test_threshold_banner_appears_only_above_ten_percent(self):
        high_entries = [
            {"page": f"unknown-{index}.md", "route": f"GET /unknown-{index}"} for index in range(11)
        ] + [
            {
                "page": f"known-{index}.md",
                "route": f"GET /known-{index}",
                "route_type": "canonical",
                "source": "metadata",
                "reason": "metadata_explicit",
            }
            for index in range(89)
        ]
        low_entries = high_entries[:5] + high_entries[11:]

        self.assertIn(
            "UNKNOWN ROUTE AUDIT THRESHOLD EXCEEDED",
            docs_index_unknown_routes.build_unknown_routes_report(self._docs_index(high_entries)),
        )
        self.assertNotIn(
            "UNKNOWN ROUTE AUDIT THRESHOLD EXCEEDED",
            docs_index_unknown_routes.build_unknown_routes_report(self._docs_index(low_entries)),
        )

    def test_report_output_is_idempotent(self):
        docs_index = self._docs_index([{"page": "a.md", "route": "GET /a"}])

        self.assertEqual(
            docs_index_unknown_routes.build_unknown_routes_report(docs_index),
            docs_index_unknown_routes.build_unknown_routes_report(docs_index),
        )

    def test_missing_docs_index_file_is_structural_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "docs-index.json"
            self.assertEqual(docs_index_unknown_routes.run_audit(missing), 1)


if __name__ == "__main__":
    unittest.main()
