import unittest
from unittest.mock import patch
import pilo


from helpers import make_context


class TestValidationFacade(unittest.TestCase):

    @patch("pilo.dataset_exists", return_value=True)
    def test_validate_existing_dataset(self, _):
        pilo.validate.dataset_exists("tank/a")


class TestValidation(unittest.TestCase):

    @patch("pilo.dataset_exists", return_value=True)
    def test_require_dataset_ok(self, _):
        pilo.require_dataset("tank/foo")

    @patch("pilo.dataset_exists", return_value=False)
    def test_require_dataset_missing(self, _):
        with self.assertRaises(SystemExit):
            pilo.require_dataset("tank/foo")

    @patch("pilo.zfs_snapshot_exists", return_value=True)
    def test_require_snapshot_ok(self, _):
        pilo.require_snapshot("tank/a@snap")

    @patch("pilo.zfs_snapshot_exists", return_value=False)
    def test_require_snapshot_missing(self, _):
        with self.assertRaises(SystemExit):
            pilo.require_snapshot("tank/a@snap")

    @patch("pilo.dataset_exists", return_value=False)
    def test_require_new_dataset_ok(self, _):
        pilo.require_new_dataset("tank/a")

    @patch("pilo.dataset_exists", return_value=True)
    def test_require_new_dataset_fail(self, _):
        with self.assertRaises(SystemExit):
            pilo.require_new_dataset("tank/a")

    @patch("pilo.zfs_snapshot_exists", return_value=True)
    def test_valid_snapshot(self, _):
        pilo.require_snapshot_of_dataset("tank/a@r1", "tank/a")

    @patch("pilo.zfs_snapshot_exists", return_value=True)
    def test_wrong_dataset_fails(self, _):
        with self.assertRaises(SystemExit):
            pilo.require_snapshot_of_dataset("tank/b@r1", "tank/a")

    def test_valid_within(self):
        pilo.require_within_dataset("tank/a/foo", "tank/a")

    def test_invalid_within(self):
        with self.assertRaises(SystemExit):
            pilo.require_within_dataset("tank/b/foo", "tank/a")

    @patch("pilo.dataset_exists", return_value=True)
    @patch("pilo.zfs_snapshot_exists", return_value=True)
    @patch("pilo.zfs_latest_snapshot", return_value="backup/a@r1")
    def test_build_plan_uses_validation(self, *_):
        cx = make_context()

        with self.assertRaises(SystemExit):
            pilo.build_recovery_plan(cx, "invalid/root")

    @patch("pilo.zfs_latest_snapshot", return_value=None)
    def test_no_source_snapshot_fails(self, _):
        with self.assertRaises(SystemExit):
            pilo.build_replication_plan("tank/a", "backup/a")

    @patch("pilo.zfs_snapshot_exists", return_value=False)
    def test_restore_requires_snapshot(self, _):
        with self.assertRaises(SystemExit):
            pilo.restore_dataset("tank/a@r1", "tank/b")
