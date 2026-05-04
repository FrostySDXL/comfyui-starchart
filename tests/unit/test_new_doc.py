import datetime
import importlib.util
import unittest
from pathlib import Path

from tests.unit.helpers.extractor_test_utils import call_main

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "new_doc.py"

spec = importlib.util.spec_from_file_location("new_doc", SCRIPT)
new_doc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(new_doc)


class TestNewDoc(unittest.TestCase):
    def _tmp_output(self, suffix, folder="reference"):
        return f"docs/{folder}/test_new_doc_{suffix}.md"

    def _clean(self, path):
        p = REPO_ROOT / Path(path)
        if p.exists():
            p.unlink()

    def _run_main(self, *args):
        return call_main(new_doc, *args)

    def test_successful_generation_replaces_primary_source(self):
        output = self._tmp_output("success", folder="tutorials")
        self._clean(output)
        exit_code, _stdout, stderr = self._run_main(
            "--output",
            output,
            "--mode",
            "tutorial",
            "--title",
            "Success Page",
            "--primary-source",
            "docs.comfy.org/tutorial",
        )
        self.assertEqual(exit_code, 0, msg=stderr)
        content = (REPO_ROOT / output).read_text(encoding="utf-8")
        self.assertIn("# Success Page", content)
        self.assertIn("**Evidence:** Source-backed from pinned snapshots", content)
        self.assertIn("**Primary Source:** docs.comfy.org/tutorial", content)
        today = datetime.date.today().isoformat()
        self.assertIn(f"**Last Updated:** {today}", content)
        self._clean(output)

    def test_evidence_override_replaces_default_label(self):
        output = self._tmp_output("evidence_override", folder="tutorials")
        self._clean(output)
        exit_code, _stdout, stderr = self._run_main(
            "--output",
            output,
            "--mode",
            "tutorial",
            "--title",
            "Evidence Override",
            "--evidence",
            "Operational guidance",
        )
        self.assertEqual(exit_code, 0, msg=stderr)
        content = (REPO_ROOT / output).read_text(encoding="utf-8")
        self.assertIn("**Evidence:** Operational guidance", content)
        self._clean(output)

    def test_invalid_mode(self):
        output = self._tmp_output("invalid_mode")
        self._clean(output)
        exit_code, _stdout, _stderr = self._run_main(
            "--output",
            output,
            "--mode",
            "invalid",
            "--title",
            "X",
        )
        self.assertNotEqual(exit_code, 0)
        self.assertFalse((REPO_ROOT / output).exists())

    def test_existing_file_refusal(self):
        output = self._tmp_output("existing")
        self._clean(output)
        (REPO_ROOT / output).write_text("existing", encoding="utf-8")
        exit_code, _stdout, _stderr = self._run_main(
            "--output",
            output,
            "--mode",
            "reference",
            "--title",
            "Existing",
        )
        self.assertNotEqual(exit_code, 0)
        self._clean(output)

    def test_output_outside_docs_rejected(self):
        exit_code, _stdout, stderr = self._run_main(
            "--output",
            "../../etc/test_new_doc_outside",
            "--mode",
            "reference",
            "--title",
            "Outside",
        )
        self.assertNotEqual(exit_code, 0)
        self.assertIn("must stay under docs/", stderr)

    def test_output_must_end_with_markdown_extension(self):
        exit_code, _stdout, stderr = self._run_main(
            "--output",
            "docs/reference/test_new_doc_no_extension",
            "--mode",
            "reference",
            "--title",
            "No Extension",
        )
        self.assertNotEqual(exit_code, 0)
        self.assertIn("must end with .md", stderr)

    def test_mode_path_mismatch_rejected_with_helpful_message(self):
        output = self._tmp_output("mismatch", folder="reference")
        self._clean(output)
        exit_code, _stdout, stderr = self._run_main(
            "--output",
            output,
            "--mode",
            "tutorial",
            "--title",
            "Mismatch",
        )
        self.assertNotEqual(exit_code, 0)
        self.assertIn("tutorial pages usually belong under", stderr)
        self.assertFalse((REPO_ROOT / output).exists())

    def test_mode_path_mismatch_can_be_overridden(self):
        output = self._tmp_output("mismatch_override", folder="reference")
        self._clean(output)
        exit_code, _stdout, stderr = self._run_main(
            "--output",
            output,
            "--mode",
            "tutorial",
            "--title",
            "Mismatch Override",
            "--allow-path-mismatch",
        )
        self.assertEqual(exit_code, 0, msg=stderr)
        self.assertTrue((REPO_ROOT / output).exists())
        self._clean(output)

    def test_scaffold_mode_warns_when_primary_source_is_unused(self):
        output = "docs/test_new_doc_scaffold.md"
        self._clean(output)
        exit_code, _stdout, stderr = self._run_main(
            "--output",
            output,
            "--mode",
            "scaffold",
            "--title",
            "Scaffold Page",
            "--primary-source",
            "docs.comfy.org/scaffold",
        )
        self.assertEqual(exit_code, 0, msg=stderr)
        self.assertIn("Primary source was provided but not used", stderr)
        content = (REPO_ROOT / output).read_text(encoding="utf-8")
        self.assertIn("# Scaffold Page", content)
        self.assertNotIn("**Primary Source:**", content)
        self._clean(output)

    def test_output_path_normalization_uses_forward_slash_shape(self):
        normalized = new_doc.normalize_output_argument(r"docs\reference\path-test.md")
        self.assertEqual(normalized.as_posix(), "docs/reference/path-test.md")


if __name__ == "__main__":
    unittest.main()
