import unittest
from unittest.mock import patch

from pilo import state
from pilo.back import replication as repl
import pilotest


class TestReplicationPlan(pilotest.TestCase):

    @patch('pilo.checks.require_dataset')
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_fails_uninitialized(self, mock_latest, *_):
        mock_latest.side_effect = ["tank/a@r1", None]

        with pilotest.assert_fatal(self):
            plan = repl.build_replication_plan("tank/a", "backup/a")

    @patch('pilo.checks.require_dataset')
    @patch("pilo.zfs.latest_snapshot")
    def test_seed_plan(self, mock_latest, *_):
        mock_latest.side_effect = [None, "tank/a@r1"]

        plan = repl.build_seed_replication_plan("tank/a", "backup/a")

        self.assertEqual(plan.mode, "seed")
        self.assertEqual(plan.snapshot, "tank/a@r1")
        self.assertIsNone(plan.base)

    @patch('pilo.checks.require_dataset')
    @patch("pilo.zfs.latest_snapshot")
    def test_seed_requires_empty_destination(self, mock_latest, *_):
        mock_latest.side_effect = ["tank/a@r1", "backup/a@r1"]
        with pilotest.assert_fatal(self):
            repl.build_seed_replication_plan("tank/a", "backup/a")

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
    def test_execute_seed(self, mock_full):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r1",
            base=None,
            mode="seed",
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


class TestReplicateCommands(pilotest.TestCase):

    def test_replicate_requires_secondary(self):
        mod = pilotest.import_command("replicate")

        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="",
        )
        cx.args = []

        with patch("pilo.context.Context", return_value=cx):
            with pilotest.assert_fatal(self):
                mod.main()

    def test_replicate_requires_attached_secondary(self):
        mod = pilotest.import_command("replicate")
        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a",
        )
        p1 = patch(
            "pilo.state.detect_system_state",
            return_value=state.DetectedSystemState(
                state=state.SystemTopologyState.REPLICA_MISSING,
                message="secondary unattached: backup/a",
                secondary=None,
            ),
        )
        p2 = patch("pilo.context.Context", return_value=cx)
        with (p1, p2, pilotest.assert_fatal(self)):
            mod.main()

    def test_replicate_safe_requires_secondary(self):
        mod = pilotest.import_command("replicate-safe")

        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="",
        )

        with patch("pilo.context.Context", return_value=cx):
            with pilotest.assert_fatal(self):
                mod.main()

    @patch("pilo.back.replication.replicate")
    def test_replicate_safe_uses_classifier_secondary(self, *_):
        mod = pilotest.import_command("replicate-safe")
        cx = pilotest.make_context()
        detected = state.DetectedSystemState(
            state=state.SystemTopologyState.REPLICATION_BEHIND,
            message="behind",
            secondary="backup/a",
        )
        p1 = patch("pilo.state.detect_system_state", return_value=detected)
        p2 = patch("pilo.context.Context", return_value=cx)
        p3 = patch("pilo.back.replication.replication_status",
                   side_effect=[
                       (repl.ReplicationStatus.BEHIND, "behind"),
                       (repl.ReplicationStatus.OK, None),
                   ])

        with (p1, p2, p3):
            mod.main()

    def test_replicate_safe_blocks_diverged_topology(self):
        mod = pilotest.import_command("replicate-safe")
        cx = pilotest.make_context()
        detected = state.DetectedSystemState(
            state=state.SystemTopologyState.REPLICATION_DIVERGED,
            message="divergence in backup/a",
            secondary="backup/a",
        )
        p1 = patch("pilo.state.detect_system_state", return_value=detected)
        p2 = patch("pilo.context.Context", return_value=cx)

        with (p1, p2, pilotest.assert_fatal(self)):
            mod.main()

    def test_replicate_verify_requires_secondary(self):
        mod = pilotest.import_command("replication-verify")

        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="",
        )

        with patch("pilo.context.Context", return_value=cx):
            with pilotest.assert_fatal(self):
                mod.main()

    @patch("pilo.back.replication.execute_replication_plan")
    @patch("pilo.back.replication.build_seed_replication_plan")
    def test_replica_seed_uses_seed_plan(self, mock_build, mock_exec):
        mod = pilotest.import_command("replica-seed")

        cx = pilotest.make_context()

        detected = state.DetectedSystemState(
            state=state.SystemTopologyState.REPLICA_UNINITIALIZED,
            message="secondary uninitialized",
            secondary="backup/a",
        )

        p1 = patch("pilo.state.detect_system_state", return_value=detected)
        p2 = patch("pilo.context.Context", return_value=cx)

        with (p1, p2):
            mod.main()

        mock_build.assert_called_once_with("tank/a", "backup/a")
        mock_exec.assert_called_once()

    def test_replicate_rejects_uninitialized_secondary(self):
        mod = pilotest.import_command("replicate")

        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a",
        )

        detected = state.DetectedSystemState(
            state=state.SystemTopologyState.REPLICA_UNINITIALIZED,
            message="secondary uninitialized",
            secondary="backup/a",
        )

        p1 = patch("pilo.state.detect_system_state", return_value=detected)
        p2 = patch("pilo.context.Context", return_value=cx)

        with (p1, p2, pilotest.assert_fatal(self)):
            mod.main()
