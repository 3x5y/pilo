import unittest
from unittest.mock import patch

from pilo import topology
import pilotest


class TestStorageTopology(pilotest.TestCase):

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists")
    def test_detect_attached_secondary(self, exists, latest):

        exists.side_effect = (
            lambda ds: ds in ("backup", "backup/a")
        )

        latest.side_effect = (
            lambda ds: "backup/a@t0"
            if ds == "backup/a"
            else None
        )

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=[
                "backup/a",
                "offline/a",
            ],
        )

        self.assertEqual(
            topo.current_secondary_root(),
            "backup/a",
        )

    @patch("pilo.zfs.dataset_exists")
    def test_no_secondary_attached(self, exists):
        exists.return_value = False

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=["backup/a"],
        )

        self.assertIsNone(
            topo.current_secondary_root(),
        )

    @patch("pilo.zfs.dataset_exists")
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

    @patch("pilo.zfs.dataset_exists")
    def test_current_secondary_dataset_multiple_attached_invalid(
        self,
        mock_exists,
    ):
        mock_exists.side_effect = (
            lambda ds: ds in (
                "backup1",
                "backup1/current",
                "backup2",
                "backup2/current",
            )
        )

        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS=(
                "backup1/current "
                "backup2/current"
            ),
        )

        with self.assertRaises(RuntimeError):
            _ = cx.current_secondary_dataset

    @patch("pilo.zfs.dataset_exists")
    def test_multiple_imported_secondaries_invalid(self, exists):

        exists.side_effect = (
            lambda ds: ds in (
                "backup1",
                "backup1/current",
                "backup2",
                "backup2/current",
            )
        )

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=[
                "backup1/current",
                "backup2/current",
            ],
        )

        with self.assertRaises(RuntimeError):
            topo.secondary_states()

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_current_secondary_dataset_none(self, _):
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="",
        )
        self.assertIsNone(cx.current_secondary_dataset)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists")
    def test_secondary_states(self, exists, latest):

        exists.side_effect = (
            lambda ds: ds in (
                "backup",
                "backup/current",
            )
        )

        latest.side_effect = (
            lambda ds: "backup/current@t0"
            if ds == "backup/current"
            else None
        )

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=[
                "offline/old",
                "backup/current",
            ],
        )

        states = topo.secondary_states()

        self.assertEqual(len(states), 2)

        old = states[0]
        self.assertEqual(old.root, "offline/old")
        self.assertFalse(old.carrier_attached)
        self.assertFalse(old.dataset_exists)
        self.assertFalse(old.initialized)
        self.assertFalse(old.current)

        cur = states[1]
        self.assertEqual(cur.root, "backup/current")
        self.assertTrue(cur.carrier_attached)
        self.assertTrue(cur.dataset_exists)
        self.assertTrue(cur.initialized)
        self.assertTrue(cur.current)

    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.zfs.dataset_exists")
    def test_current_secondary_state(self, exists, latest):

        exists.side_effect = (
            lambda ds: ds in (
                "backup",
                "backup/current",
            )
        )

        latest.side_effect = (
            lambda ds: "backup/current@t0"
            if ds == "backup/current"
            else None
        )

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=[
                "offline/old",
                "backup/current",
            ],
        )

        state = topo.current_secondary_state()

        self.assertIsNotNone(state)
        self.assertEqual(state.root, "backup/current")
        self.assertTrue(state.current)
