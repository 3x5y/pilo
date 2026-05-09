import unittest
from unittest.mock import patch

from pilo.back import replication as repl
import pilotest


class TestReplicationPlan(unittest.TestCase):

    @patch('pilo.checks.require_dataset')
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_full_when_dst_empty(self, mock_latest, *_):
        mock_latest.side_effect = ["tank/a@r1", None]

        plan = repl.build_replication_plan("tank/a", "backup/a")

        self.assertEqual(plan.src, "tank/a")
        self.assertEqual(plan.dst, "backup/a")
        self.assertEqual(plan.mode, "full")
        self.assertEqual(plan.snapshot, "tank/a@r1")
        self.assertIsNone(plan.base)

    @patch('pilo.checks.require_dataset')
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_incremental(self, mock_latest, mock_base, *_):
        mock_latest.side_effect = ["tank/a@r2", "backup/a@r1"]
        mock_base.return_value = "tank/a@r1"

        plan = repl.build_replication_plan("tank/a", "backup/a")

        self.assertEqual(plan.mode, "incremental")
        self.assertEqual(plan.base, "tank/a@r1")
        self.assertEqual(plan.snapshot, "tank/a@r2")

    @patch('pilo.checks.require_dataset')
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_noop_when_up_to_date(self, mock_latest, mock_base, *_):
        mock_latest.side_effect = ["tank/a@r1", "backup/a@r1"]
        mock_base.return_value = "tank/a@r1"

        plan = repl.build_replication_plan("tank/a", "backup/a")

        self.assertEqual(plan.mode, "noop")

    @patch("pilo.zfs.replicate_full")
    def test_execute_full(self, mock_full):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r1",
            base=None,
            mode="full",
        )

        repl.execute_replication_plan(plan)

        mock_full.assert_called_once_with("tank/a@r1", "backup/a")

    @patch("pilo.zfs.replicate_incremental")
    def test_execute_incremental(self, mock_incr):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r2",
            base="tank/a@r1",
            mode="incremental",
        )

        repl.execute_replication_plan(plan)

        mock_incr.assert_called_once_with(
            "tank/a@r1",
            "tank/a@r2",
            "backup/a",
        )

    @patch("pilo.back.replication.execute_replication_plan")
    @patch("pilo.back.replication.build_replication_plan")
    def test_replicate_uses_plan(self, mock_build, mock_exec):
        mock_build.return_value = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r1",
            base=None,
            mode="full",
        )

        repl.replicate("tank/a", "backup/a")

        mock_build.assert_called_once_with("tank/a", "backup/a")
        mock_exec.assert_called_once()

    @patch("pilo.zfs.latest_snapshot", return_value=None)
    def test_no_source_snapshot_fails(self, _):
        with pilotest.assert_fatal(self):
            repl.build_replication_plan("tank/a", "backup/a")

