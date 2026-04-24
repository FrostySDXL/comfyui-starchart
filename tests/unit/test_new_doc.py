import datetime
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "new_doc.py"


class TestNewDoc(unittest.TestCase):
    def _tmp_output(self, suffix):
        return f"docs/test_new_doc_{suffix}.md"

    def _clean(self, path):
        p = REPO_ROOT / path
        if p.exists():
            p.unlink()

    def test_successful_generation(self):
        output = self._tmp_output("success")
        self._clean(output)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output",
                output,
                "--mode",
                "reference",
                "--title",
                "Success Page",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((REPO_ROOT / output).exists())
        content = (REPO_ROOT / output).read_text(encoding="utf-8")
        self.assertIn("# Success Page", content)
        self._clean(output)

    def test_invalid_mode(self):
        output = self._tmp_output("invalid_mode")
        self._clean(output)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output",
                output,
                "--mode",
                "invalid",
                "--title",
                "X",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((REPO_ROOT / output).exists())

    def test_existing_file_refusal(self):
        output = self._tmp_output("existing")
        self._clean(output)
        (REPO_ROOT / output).write_text("existing", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output",
                output,
                "--mode",
                "reference",
                "--title",
                "Existing",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self._clean(output)

    def test_output_outside_docs_rejected(self):
        output = self._tmp_output("outside")
        self._clean(output)
        # Use a path that resolves outside docs/ -- "../../etc/foo" is one way
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output",
                "../../etc/test_new_doc_outside",
                "--mode",
                "reference",
                "--title",
                "Outside",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be under docs/", result.stderr)
        self.assertFalse((REPO_ROOT / output).exists())

    def test_placeholder_substitution(self):
        output = self._tmp_output("subst")
        self._clean(output)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output",
                output,
                "--mode",
                "scaffold",
                "--title",
                "Subst Page",
                "--evidence",
                "Operational guidance",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        content = (REPO_ROOT / output).read_text(encoding="utf-8")
        self.assertIn("# Subst Page", content)
        today = datetime.date.today().isoformat()
        self.assertIn(f"**Last Updated:** {today}", content)
        self.assertIn("**Evidence:** Operational guidance", content)
        self._clean(output)


if __name__ == "__main__":
    unittest.main()
