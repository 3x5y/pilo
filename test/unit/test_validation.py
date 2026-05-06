import unittest
from unittest.mock import patch
import pilo


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


class TestValidationFacade(unittest.TestCase):

    @patch("pilo.dataset_exists", return_value=True)
    def test_validate_existing_dataset(self, _):
        pilo.validate.dataset_exists("tank/a")
