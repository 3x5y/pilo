import unittest
from unittest.mock import patch

from pilo import util
from pilo.back import snapshot
import pilotest


class TestSnapshotPolicy(pilotest.TestCase):

    def test_policy_builds_name(self):
        policy = snapshot.SnapshotPolicy(prefix="r")

        name = policy.build_name("20240101_000000_000000")

        self.assertEqual(name, "r-20240101_000000_000000")

    def test_policy_no_timestamp_for_raw(self):
        policy = snapshot.SnapshotPolicy(prefix="x", raw=True)

        name = policy.build_name("TS")

        self.assertEqual(name, "x")

    @patch("pilo.util.snapshot_timestamp", return_value="TS")
    def test_policy_uses_timestamp(self, mock_ts):
        policy = snapshot.SnapshotPolicy(prefix="x")

        name = policy.build_name(util.snapshot_timestamp())

        self.assertEqual(name, "x-TS")

    @patch("pilo.zfs.snapshot")
    def test_creates_snapshot(self, mock_snap):
        policy = snapshot.SnapshotPolicy(prefix="r")

        snap = snapshot.create_snapshot_with_policy(policy, "tank/a", ts="TS")

        mock_snap.assert_called_once_with("r-TS", "tank/a")
        self.assertEqual(snap, "tank/a@r-TS")

    @patch("pilo.back.snapshot.create_snapshot_with_policy")
    def test_prefixed_uses_policy(self, mock_create):
        mock_create.return_value = "tank/a@r-TS"

        snap = snapshot.create_prefixed_snapshot("r", "tank/a")

        self.assertEqual(snap, "tank/a@r-TS")
        mock_create.assert_called_once()

    @patch("pilo.back.snapshot.create_snapshot_with_policy")
    def test_create_snapshot_uses_policy(self, mock_create):
        mock_create.return_value = "tank/a@foo"

        snap = snapshot.create_snapshot("foo", "tank/a")

        self.assertEqual(snap, "tank/a@foo")
