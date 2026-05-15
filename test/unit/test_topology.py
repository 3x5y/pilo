import unittest
from unittest import mock

from pilo import topology


class TestStorageTopology(unittest.TestCase):

    @mock.patch("pilo.zfs.dataset_exists")
    def test_detect_attached_secondary(self, exists):
        exists.side_effect = lambda ds: ds == "backup/b"

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=[
                "backup/a",
                "backup/b",
            ],
        )

        self.assertEqual(
            topo.current_secondary_root(),
            "backup/b",
        )

    @mock.patch("pilo.zfs.dataset_exists")
    def test_no_secondary_attached(self, exists):
        exists.return_value = False

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=["backup/a"],
        )

        self.assertIsNone(
            topo.current_secondary_root(),
        )

    @mock.patch("pilo.zfs.dataset_exists")
    def test_multiple_secondaries_fail(self, exists):
        exists.return_value = True

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=[
                "backup/a",
                "backup/b",
            ],
        )

        with self.assertRaises(RuntimeError):
            topo.current_secondary_root()
