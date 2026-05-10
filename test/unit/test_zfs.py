import subprocess
import unittest
from unittest.mock import patch, Mock

from pilo import zfs


class TestZfsRun(unittest.TestCase):

    @patch("subprocess.run")
    def test_zfs_run_default_check_true(self, run):
        proc = Mock()
        proc.stdout = ""
        run.return_value = proc

        zfs.run(["zfs", "list"])

        _, kwargs = run.call_args
        self.assertEqual(kwargs["check"], True)

    @patch("subprocess.run")
    def test_zfs_run_capture_text(self, run):
        proc = Mock()
        proc.stdout = ""
        run.return_value = proc

        zfs.run(["zfs", "list"], capture_output=True)

        _, kwargs = run.call_args
        self.assertEqual(kwargs["capture_output"], True)
        self.assertEqual(kwargs["text"], True)

    @patch("subprocess.run")
    def test_dataset_exists_uses_check_false(self, run):
        proc = Mock()
        proc.returncode = 1
        run.return_value = proc

        zfs.dataset_exists("tank/missing")

        _, kwargs = run.call_args
        self.assertEqual(kwargs["check"], False)
