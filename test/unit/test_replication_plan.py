import unittest
from unittest.mock import patch

import pilo


class TestReplicationPlan(unittest.TestCase):

    @patch("pilo.zfs.latest_snapshot")
    def test_plan_full_when_dst_empty(self, mock_latest):
        mock_latest.side_effect = ["tank/a@r1", None]

        plan = pilo.build_replication_plan("tank/a", "backup/a")

        self.assertEqual(plan.src, "tank/a")
        self.assertEqual(plan.dst, "backup/a")
        self.assertEqual(plan.mode, "full")
        self.assertEqual(plan.snapshot, "tank/a@r1")
        self.assertIsNone(plan.base)

    @patch("pilo.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_incremental(self, mock_latest, mock_base):
        mock_latest.side_effect = ["tank/a@r2", "backup/a@r1"]
        mock_base.return_value = "tank/a@r1"

        plan = pilo.build_replication_plan("tank/a", "backup/a")

        self.assertEqual(plan.mode, "incremental")
        self.assertEqual(plan.base, "tank/a@r1")
        self.assertEqual(plan.snapshot, "tank/a@r2")

    @patch("pilo.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_noop_when_up_to_date(self, mock_latest, mock_base):
        mock_latest.side_effect = ["tank/a@r1", "backup/a@r1"]
        mock_base.return_value = "tank/a@r1"

        plan = pilo.build_replication_plan("tank/a", "backup/a")

        self.assertEqual(plan.mode, "noop")

    @patch("pilo.zfs.replicate_full")
    def test_execute_full(self, mock_full):
        plan = pilo.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r1",
            base=None,
            mode="full",
        )

        pilo.execute_replication_plan(plan)

        mock_full.assert_called_once_with("tank/a@r1", "backup/a")

    @patch("pilo.zfs.replicate_incremental")
    def test_execute_incremental(self, mock_incr):
        plan = pilo.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r2",
            base="tank/a@r1",
            mode="incremental",
        )

        pilo.execute_replication_plan(plan)

        mock_incr.assert_called_once_with(
            "tank/a@r1",
            "tank/a@r2",
            "backup/a",
        )

    @patch("pilo.execute_replication_plan")
    @patch("pilo.build_replication_plan")
    def test_replicate_uses_plan(self, mock_build, mock_exec):
        mock_build.return_value = pilo.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r1",
            base=None,
            mode="full",
        )

        pilo.replicate("tank/a", "backup/a")

        mock_build.assert_called_once_with("tank/a", "backup/a")
        mock_exec.assert_called_once()
