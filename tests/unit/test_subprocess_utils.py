from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from scripts.common import subprocess_utils


class SubprocessUtilsTests(unittest.TestCase):
    def test_run_step_success(self):
        with patch("scripts.common.subprocess_utils.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                ["echo", "ok"], 0, stdout="ok\n", stderr=""
            )
            self.assertTrue(subprocess_utils.run_step(["echo", "ok"], "Echo step"))

    def test_run_step_failure(self):
        with patch("scripts.common.subprocess_utils.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                ["false"], 1, stdout="", stderr="boom"
            )
            self.assertFalse(subprocess_utils.run_step(["false"], "Failing step"))
