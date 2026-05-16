import unittest
from unittest.mock import patch

from pilo import topology
import pilotest


class TestStorageTopology(pilotest.TestCase):

    @patch("pilo.zfs.dataset_exists")
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
    def test_current_secondary_dataset_prefers_topology(self, mock_exists):
        mock_exists.side_effect = lambda ds: ds == "backup/current"
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/old backup/current",
            PILO_REPLICA_ROOT="backup/legacy",
        )
        self.assertEqual("backup/current", cx.current_secondary_dataset)

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_current_secondary_dataset_fallback(self, _):
        cx = pilotest.make_context(
            PILO_REPLICA_ROOT="backup/legacy",
        )
        self.assertEqual("backup/legacy", cx.current_secondary_dataset)

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_current_secondary_dataset_none(self, _):
        cx = pilotest.make_context(
            PILO_REPLICA_ROOT="",
        )
        self.assertIsNone(cx.current_secondary_dataset)

    @patch("pilo.zfs.dataset_exists")
    def test_secondary_states(self, exists):
        exists.side_effect = lambda ds: ds == "backup/current"

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=[
                "backup/old",
                "backup/current",
            ],
        )

        states = topo.secondary_states()

        self.assertEqual(len(states), 2)

        old = states[0]
        self.assertEqual(old.root, "backup/old")
        self.assertTrue(old.configured)
        self.assertFalse(old.attached)
        self.assertFalse(old.initialized)
        self.assertFalse(old.current)

        cur = states[1]
        self.assertEqual(cur.root, "backup/current")
        self.assertTrue(cur.configured)
        self.assertTrue(cur.attached)
        self.assertTrue(cur.initialized)
        self.assertTrue(cur.current)

    @patch("pilo.zfs.dataset_exists")
    def test_current_secondary_state(self, exists):
        exists.side_effect = lambda ds: ds == "backup/current"

        topo = topology.StorageTopology(
            primary_root="tank/a",
            secondary_roots=[
                "backup/old",
                "backup/current",
            ],
        )

        state = topo.current_secondary_state()

        self.assertIsNotNone(state)
        self.assertEqual(state.root, "backup/current")
        self.assertTrue(state.current)

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_current_secondary_state_compat_fallback(self, _):
        cx = pilotest.make_context(
            PILO_REPLICA_ROOT="backup/legacy",
        )

        state = cx.current_secondary_state

        self.assertEqual(state.root, "backup/legacy")
        self.assertFalse(state.attached)
        self.assertFalse(state.initialized)
        self.assertFalse(state.current)
