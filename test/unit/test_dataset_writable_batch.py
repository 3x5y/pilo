import unittest
from unittest.mock import patch, call

from pilo.fs import writable_datasets


class TestWritableDatasets(unittest.TestCase):

    @patch("pilo.zfs.set_readonly")
    @patch("pilo.zfs.get_readonly")
    def test_enables_all_readonly_datasets(
        self,
        mock_get,
        mock_set,
    ):
        mock_get.side_effect = [True, True]

        with writable_datasets([
            "tank/a",
            "tank/b",
        ]):
            pass

        self.assertEqual(
            mock_set.mock_calls,
            [
                call("tank/a", False),
                call("tank/b", False),
                call("tank/b", True),
                call("tank/a", True),
            ]
        )

    @patch("pilo.zfs.set_readonly")
    @patch("pilo.zfs.get_readonly")
    def test_deduplicates_datasets(
        self,
        mock_get,
        mock_set,
    ):
        mock_get.return_value = True

        with writable_datasets([
            "tank/a",
            "tank/a",
        ]):
            pass

        self.assertEqual(
            mock_set.mock_calls,
            [
                call("tank/a", False),
                call("tank/a", True),
            ]
        )
