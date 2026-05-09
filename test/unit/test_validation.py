from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pilo import validation
from pilo.back import restore
from pilo.back import recover
from pilo.back import replication as repl
import pilotest


class TestValidationFacade(unittest.TestCase):

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_validate_existing_dataset(self, _):
        validation.validate.dataset_exists("tank/a")


class TestValidation(unittest.TestCase):

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_require_dataset_ok(self, _):
        validation.require_dataset("tank/foo")

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_require_dataset_missing(self, _):
        with pilotest.assert_fatal(self):
            validation.require_dataset("tank/foo")

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    def test_require_snapshot_ok(self, _):
        validation.require_snapshot("tank/a@snap")

    @patch("pilo.zfs.snapshot_exists", return_value=False)
    def test_require_snapshot_missing(self, _):
        with pilotest.assert_fatal(self):
            validation.require_snapshot("tank/a@snap")

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_require_new_dataset_ok(self, _):
        validation.require_new_dataset("tank/a")

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_require_new_dataset_fail(self, _):
        with pilotest.assert_fatal(self):
            validation.require_new_dataset("tank/a")

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    def test_valid_snapshot(self, _):
        validation.require_snapshot_of_dataset("tank/a@r1", "tank/a")

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    def test_wrong_dataset_fails(self, _):
        with pilotest.assert_fatal(self):
            validation.require_snapshot_of_dataset("tank/b@r1", "tank/a")

    def test_valid_within(self):
        validation.require_within_dataset("tank/a/foo", "tank/a")

    def test_invalid_within(self):
        with pilotest.assert_fatal(self):
            validation.require_within_dataset("tank/b/foo", "tank/a")

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.latest_snapshot", return_value="backup/a@r1")
    def test_build_plan_uses_validation(self, *_):
        cx = pilotest.make_context()

        with pilotest.assert_fatal(self):
            recover.build_recovery_plan(cx, "invalid/root")

    @patch("pilo.zfs.latest_snapshot", return_value=None)
    def test_no_source_snapshot_fails(self, _):
        with pilotest.assert_fatal(self):
            repl.build_replication_plan("tank/a", "backup/a")

    @patch("pilo.zfs.snapshot_exists", return_value=False)
    def test_restore_requires_snapshot(self, _):
        with pilotest.assert_fatal(self):
            restore.restore_dataset("tank/a@r1", "tank/b")

    def test_require_file_accepts_existing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "a.txt"
            path.write_text("x")

            validation.require_file(path)

    def test_require_file_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "missing.txt"

            with pilotest.assert_fatal(self):
                validation.require_file(path)

    def test_require_no_conflict_accepts_missing_target(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            dst = Path(td) / "dst.txt"

            src.write_text("x")

            validation.require_no_conflict(src, dst)

    def test_require_no_conflict_accepts_identical_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            dst = Path(td) / "dst.txt"

            src.write_text("same")
            dst.write_text("same")

            validation.require_no_conflict(src, dst)

    def test_require_no_conflict_rejects_different_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src.txt"
            dst = Path(td) / "dst.txt"

            src.write_text("a")
            dst.write_text("b")

            with pilotest.assert_fatal(self):
                validation.require_no_conflict(src, dst)
