import unittest
from unittest.mock import patch

import pilo


class TestSnapshotPolicy(unittest.TestCase):

    def test_policy_builds_name(self):
        policy = pilo.SnapshotPolicy(prefix="r")

        name = policy.build_name("20240101_000000_000000")

        self.assertEqual(name, "r-20240101_000000_000000")

    @patch("pilo.snapshot_timestamp", return_value="TS")
    def test_policy_uses_timestamp(self, mock_ts):
        policy = pilo.SnapshotPolicy(prefix="x")

        name = policy.build_name(pilo.snapshot_timestamp())

        self.assertEqual(name, "x-TS")

    @patch("pilo.zfs_snapshot")
    def test_creates_snapshot(self, mock_snap):
        policy = pilo.SnapshotPolicy(prefix="r")

        snap = pilo.create_snapshot_with_policy(policy, "tank/a", ts="TS")

        mock_snap.assert_called_once_with("r-TS", "tank/a")
        self.assertEqual(snap, "tank/a@r-TS")

    @patch("pilo.create_snapshot_with_policy")
    def test_prefixed_uses_policy(self, mock_create):
        mock_create.return_value = "tank/a@r-TS"

        snap = pilo.create_prefixed_snapshot("r", "tank/a")

        self.assertEqual(snap, "tank/a@r-TS")
        mock_create.assert_called_once()

    @patch("pilo.create_snapshot_with_policy")
    def test_rotation_anchor_sets_hold(self, mock_create):
        mock_create.return_value = "tank/a@rotation-TS"

        snap = pilo.create_anchor("rotation", "tank/a")

        policy = mock_create.call_args[0][0]
        self.assertTrue(policy.hold)

    @patch("pilo.create_snapshot_with_policy")
    def test_create_snapshot_uses_policy(self, mock_create):
        mock_create.return_value = "tank/a@foo"

        snap = pilo.create_snapshot("foo", "tank/a")

        self.assertEqual(snap, "tank/a@foo")

    @patch("pilo.zfs_hold")
    @patch("pilo.zfs_snapshot")
    def test_hold_applied(self, mock_snap, mock_hold):
        policy = pilo.SnapshotPolicy(prefix="x", hold=True)

        snap = pilo.create_snapshot_with_policy(policy, "tank/a", ts="TS")

        mock_hold.assert_called_once_with("repl-anchor", "tank/a@x-TS")
