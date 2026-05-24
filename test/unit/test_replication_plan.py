from pathlib import Path
import unittest
from unittest.mock import patch

from pilo import lifecycle
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

        mock_full.assert_called_once_with(
            "tank/a@r1", "backup/a", tee_path=None,
        )

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
            tee_path=None,
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

    @patch("pilo.lifecycle.detect_lifecycle")
    @patch("pilo.back.replication.build_seed_replication_plan")
    def test_build_replica_seed_plan(self, mock_build, mock_detect):
        cx = pilotest.make_context()

        mock_detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICA_UNINITIALIZED,
            secondary="backup/a",
        )

        repl.build_replica_seed_plan(cx)

        mock_build.assert_called_once_with(
            "tank/a",
            "backup/a",
            label="backup",
        )

    @patch("pilo.lifecycle.detect_lifecycle")
    def test_build_replica_seed_plan_rejects_normal(self, mock_detect):
        cx = pilotest.make_context()

        mock_detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
            secondary="backup/a",
        )

        with pilotest.assert_fatal(self):
            repl.build_replica_seed_plan(cx)


class TestReplicationPlanExport(pilotest.TestCase):

    @patch("pilo.back.replication._resolve_export_path",
           return_value="/out/ts-incr.zfs")
    @patch("pilo.checks.require_dataset")
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_export_true_sets_export_path(
        self, mock_latest, mock_base, *_,
    ):
        mock_latest.side_effect = ["tank/a@ts-incr", "backup/a@ts-incr"]
        mock_base.return_value = "tank/a@ts-incr"

        plan = repl.build_replication_plan(
            "tank/a", "backup/a", export=True,
        )

        self.assertEqual(plan.export_path, "/out/ts-incr.zfs")

    @patch("pilo.checks.require_dataset")
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_export_false_leaves_export_path_none(
        self, mock_latest, mock_base, *_,
    ):
        mock_latest.side_effect = ["tank/a@ts-incr", "backup/a@ts-incr"]
        mock_base.return_value = "tank/a@ts-incr"

        plan = repl.build_replication_plan(
            "tank/a", "backup/a", export=False,
        )

        self.assertIsNone(plan.export_path)

    @patch("pilo.back.replication._resolve_export_path",
           return_value=None)
    @patch("pilo.checks.require_dataset")
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_export_true_non_canonical_returns_none(
        self, mock_latest, mock_base, *_,
    ):
        mock_latest.side_effect = ["tank/a@r-ts", "backup/a@r-ts"]
        mock_base.return_value = "tank/a@r-ts"

        plan = repl.build_replication_plan(
            "tank/a", "backup/a", export=True,
        )

        self.assertIsNone(plan.export_path)


class TestReplicationPlanWithLabel(pilotest.TestCase):

    @patch("pilo.checks.require_dataset")
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_incremental_with_label(self, mock_latest, mock_base, *_):
        mock_latest.side_effect = ["tank/a@r2", "backup/a@r1"]
        mock_base.return_value = "tank/a@r1"

        plan = repl.build_replication_plan(
            "tank/a", "backup/a", label="mylabel"
        )

        self.assertEqual(plan.mode, "incremental")
        self.assertEqual(plan.hold_snapshot, "tank/a@r2")
        self.assertEqual(plan.hold_tag, "pilo:mylabel")

    @patch("pilo.checks.require_dataset")
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_seed_with_label(self, mock_latest, *_):
        mock_latest.side_effect = [None, "tank/a@r1"]

        plan = repl.build_seed_replication_plan(
            "tank/a", "backup/a", label="mylabel"
        )

        self.assertEqual(plan.mode, "seed")
        self.assertEqual(plan.hold_snapshot, "tank/a@r1")
        self.assertEqual(plan.hold_tag, "pilo:mylabel")

    @patch("pilo.back.replication._has_continuity_hold", return_value=True)
    @patch("pilo.checks.require_dataset")
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_noop_with_label_hold_ok(
        self, mock_latest, mock_base, *_
    ):
        mock_latest.side_effect = ["tank/a@r1", "backup/a@r1"]
        mock_base.return_value = "tank/a@r1"

        plan = repl.build_replication_plan(
            "tank/a", "backup/a", label="mylabel"
        )

        self.assertEqual(plan.mode, "noop")

    @patch("pilo.back.replication._has_continuity_hold", return_value=False)
    @patch("pilo.checks.require_dataset")
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.latest_snapshot")
    def test_plan_noop_with_label_hold_missing_fatal(
        self, mock_latest, mock_base, *_
    ):
        mock_latest.side_effect = ["tank/a@r1", "backup/a@r1"]
        mock_base.return_value = "tank/a@r1"

        with pilotest.assert_fatal(self):
            repl.build_replication_plan(
                "tank/a", "backup/a", label="mylabel"
            )

    @patch("pilo.zfs.hold")
    @patch("pilo.zfs.replicate_full")
    def test_execute_seed_applies_hold(self, mock_full, mock_hold):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r1",
            base=None,
            mode="seed",
            hold_snapshot="tank/a@r1",
            hold_tag="pilo:z1",
        )

        repl.execute_replication_plan(plan)

        mock_hold.assert_called_once_with("pilo:z1", "tank/a@r1")
        mock_full.assert_called_once_with(
            "tank/a@r1", "backup/a", tee_path=None,
        )

    @patch("pilo.zfs.hold")
    @patch("pilo.zfs.replicate_incremental")
    def test_execute_incremental_applies_hold(self, mock_incr, mock_hold):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r2",
            base="tank/a@r1",
            mode="incremental",
            hold_snapshot="tank/a@r2",
            hold_tag="pilo:z1",
        )

        repl.execute_replication_plan(plan)

        mock_hold.assert_called_once_with("pilo:z1", "tank/a@r2")
        mock_incr.assert_called_once_with(
            "tank/a@r1", "tank/a@r2", "backup/a",
            tee_path=None,
        )


class TestExecuteWithExportPath(pilotest.TestCase):

    @patch("pilo.back.streams.write_stream_manifest")
    @patch("pilo.zfs.get_guid", return_value="g")
    @patch("pilo.zfs.replicate_full")
    def test_seed_forwards_export_path(
        self, mock_full, mock_guid, mock_manifest,
    ):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r1",
            base=None,
            mode="seed",
            export_path="/out/s.zfs",
        )

        repl.execute_replication_plan(plan)

        mock_full.assert_called_once_with(
            "tank/a@r1", "backup/a", tee_path="/out/s.zfs",
        )

    @patch("pilo.zfs.recv_file")
    @patch("pilo.back.streams.verify_one", return_value=("OK", ""))
    @patch("pilo.back.streams.write_stream_manifest")
    @patch("pilo.zfs.get_guid", return_value="g")
    @patch("pilo.zfs.send_incremental_to_file")
    def test_incremental_forwards_export_path(
        self, mock_send, mock_guid, mock_manifest, mock_verify, mock_recv
    ):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r2",
            base="tank/a@r1",
            mode="incremental",
            export_path="/out/s.zfs",
        )

        repl.execute_replication_plan(plan)

        mock_send.assert_called_once_with(
            "tank/a@r1", "tank/a@r2", "/out/s.zfs",
        )
        mock_verify.assert_called_once_with(Path("/out/s.zfs"))
        mock_recv.assert_called_once_with("/out/s.zfs", "backup/a")

    @patch("pilo.zfs.replicate_full")
    def test_noop_skips_export(self, mock_full):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r1",
            base="tank/a@r1",
            mode="noop",
            export_path="/out/s.zfs",
        )

        repl.execute_replication_plan(plan)

        mock_full.assert_not_called()

    @patch("pilo.back.streams.write_stream_manifest")
    @patch("pilo.zfs.get_guid", return_value="guid_seed")
    @patch("pilo.zfs.replicate_full")
    def test_seed_writes_manifest(
        self, mock_full, mock_guid, mock_manifest,
    ):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@ts-incr",
            base=None,
            mode="seed",
            export_path="/out/s.zfs",
        )

        repl.execute_replication_plan(plan)

        mock_guid.assert_called_once_with("tank/a@ts-incr")
        mock_manifest.assert_called_once_with(
            Path("/out/s.zfs"), "ts-incr", "tank/a", "guid_seed",
        )

    @patch("pilo.zfs.set_prop")
    @patch("pilo.zfs.recv_file")
    @patch("pilo.back.streams.verify_one", return_value=("OK", ""))
    @patch("pilo.back.streams.write_stream_manifest")
    @patch("pilo.zfs.get_guid", return_value="guid_incr")
    @patch("pilo.zfs.send_incremental_to_file")
    def test_incremental_writes_manifest(
        self, mock_send, mock_guid, mock_manifest, mock_verify, mock_recv, mock_setprop,
    ):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@ts-incr",
            base="tank/a@base",
            mode="incremental",
            export_path="/out/s.zfs",
        )

        repl.execute_replication_plan(plan)

        mock_guid.assert_called_once_with("tank/a@ts-incr")
        mock_manifest.assert_called_once_with(
            Path("/out/s.zfs"), "ts-incr", "tank/a", "guid_incr",
        )

    @patch("pilo.back.streams.write_stream_manifest")
    @patch("pilo.zfs.get_guid")
    @patch("pilo.zfs.replicate_full")
    def test_noop_skips_manifest(
        self, mock_full, mock_guid, mock_manifest,
    ):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@ts-incr",
            base="tank/a@ts-incr",
            mode="noop",
            export_path="/out/s.zfs",
        )

        repl.execute_replication_plan(plan)

        mock_full.assert_not_called()
        mock_guid.assert_not_called()
        mock_manifest.assert_not_called()

    @patch("pilo.zfs.replicate_full")
    def test_seed_no_export_skips_manifest(self, mock_full):
        plan = repl.ReplicationPlan(
            src="tank/a",
            dst="backup/a",
            snapshot="tank/a@r1",
            base=None,
            mode="seed",
        )

        repl.execute_replication_plan(plan)

        mock_full.assert_called_once_with(
            "tank/a@r1", "backup/a", tee_path=None,
        )


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
            "pilo.lifecycle.detect_lifecycle",
            return_value=lifecycle.LifecycleStatus(
                state=lifecycle.LifecycleState.REPLICA_MISSING,
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
    @patch("pilo.back.replication.build_replication_plan")
    @patch("pilo.back.replication.execute_replication_plan")
    def test_replicate_safe_uses_classifier_secondary(self, *_):
        mod = pilotest.import_command("replicate-safe")
        cx = pilotest.make_context()
        detected = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_BEHIND,
            message="behind",
            secondary="backup/a",
        )
        p1 = patch("pilo.lifecycle.detect_lifecycle", return_value=detected)
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
        detected = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_DIVERGED,
            message="divergence in backup/a",
            secondary="backup/a",
        )
        p1 = patch("pilo.lifecycle.detect_lifecycle", return_value=detected)
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

        detected = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICA_UNINITIALIZED,
            message="secondary uninitialized",
            secondary="backup/a",
        )

        p1 = patch("pilo.lifecycle.detect_lifecycle", return_value=detected)
        p2 = patch("pilo.context.Context", return_value=cx)

        with (p1, p2):
            mod.main()

        mock_build.assert_called_once_with("tank/a", "backup/a", label="backup")
        mock_exec.assert_called_once()

    def test_replicate_rejects_uninitialized_secondary(self):
        mod = pilotest.import_command("replicate")

        cx = pilotest.make_context(
            PILO_SECONDARY_ROOTS="backup/a",
        )

        detected = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICA_UNINITIALIZED,
            message="secondary uninitialized",
            secondary="backup/a",
        )

        p1 = patch("pilo.lifecycle.detect_lifecycle", return_value=detected)
        p2 = patch("pilo.context.Context", return_value=cx)

        with (p1, p2, pilotest.assert_fatal(self)):
            mod.main()

    @patch("pilo.lifecycle.detect_lifecycle")
    def test_replicate_safe_rejects_diverged(self, detect):
        detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICATION_DIVERGED,
            message="diverged",
            secondary="backup/a",
        )
        cx = pilotest.make_context()
        p1 = patch("pilo.context.Context", return_value=cx)
        mod = pilotest.import_command("replicate-safe")

        with (p1, pilotest.assert_fatal(self)):
            mod.main()

    @patch("pilo.lifecycle.detect_lifecycle")
    def test_replicate_rejects_uninitialized(self, detect):
        detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.REPLICA_UNINITIALIZED,
            secondary="backup/a",
        )
        cx = pilotest.make_context()
        p1 = patch("pilo.context.Context", return_value=cx)
        mod = pilotest.import_command("replicate")

        with (p1, pilotest.assert_fatal(self)):
            mod.main()


class TestReplicationState(pilotest.TestCase):

    @patch("pilo.zfs.get_latest_guid", return_value=None)
    def test_incr_base_none(self, *_):
        base = repl.find_incremental_base("tank/a", "backup/a")
        self.assertIsNone(base)

    @patch("pilo.zfs.get_latest_guid", return_value=1)
    @patch("pilo.zfs.snapshot_guids")
    def test_incr_base_simple(self, guid, *_):
        guid.return_value = [
            ['tank/a@t0', 1]
        ]
        base = repl.find_incremental_base("tank/a", "backup/a")
        self.assertEqual(base, "tank/a@t0")

    @patch("pilo.zfs.get_latest_guid", return_value=1)
    @patch("pilo.zfs.snapshot_guids")
    def test_incr_base_many(self, guid, *_):
        guid.return_value = [
            ["tank/a@t1", 2],
            ['tank/a@t0', 1]
        ]
        base = repl.find_incremental_base("tank/a", "backup/a")
        self.assertEqual(base, "tank/a@t0")

    @patch("pilo.zfs.get_latest_guid", return_value=1)
    @patch("pilo.zfs.snapshot_guids")
    def test_incr_base_no_match(self, guid, *_):
        guid.return_value = [
            ["tank/a@t1", 2],
            ['tank/a@t0', 3]
        ]
        base = repl.find_incremental_base("tank/a", "backup/a")
        self.assertIsNone(base)

    @patch("pilo.zfs.get_latest_guid", side_effect=['guid', None])
    def test_empty_replica(self, *_):

        status, msg = repl.replication_state("tank/a", "backup/a")

        self.assertEqual(status, repl.ReplicationStatus.EMPTY)
        self.assertEqual(msg, "replica is uninitialized")

    @patch("pilo.zfs.get_latest_guid", side_effect=[None, 1])
    def test_missing_source_snapshots(self, *_):

        status, msg = repl.replication_state("tank/a", "backup/a")

        self.assertEqual(status, repl.ReplicationStatus.UNKNOWN)
        self.assertEqual(msg, "source has no snapshots")

    @patch("pilo.zfs.list_filesystems",
           return_value=["backup/a"])
    @patch("pilo.back.replication.find_incremental_base",
           return_value="tank/a@t0")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.get_latest_guid", side_effect=[1, 2, 1, 2])
    @patch("pilo.context.DatasetMapping")
    def test_behind(self, Mapping, *_):

        mapping = Mapping.return_value
        mapping.inverse.return_value = "tank/a"
        status, msg = repl.replication_state("tank/a", "backup/a")

        self.assertEqual(status, repl.ReplicationStatus.BEHIND)
        self.assertEqual(msg, "behind in backup/a")

    @patch("pilo.zfs.list_filesystems",
           return_value=["backup/a"])
    @patch("pilo.back.replication.find_incremental_base",
           return_value=None)
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.get_latest_guid", side_effect=[1, 1])
    @patch("pilo.context.DatasetMapping")
    def test_no_base(self, Mapping, *_):

        mapping = Mapping.return_value
        mapping.inverse.return_value = "tank/a"
        status, msg = repl.replication_state("tank/a", "backup/a")

        self.assertEqual(status, repl.ReplicationStatus.DIVERGED)
        self.assertEqual(msg, "divergence in backup/a")

    @patch("pilo.zfs.list_filesystems",
           return_value=["backup/a"])
    @patch("pilo.back.replication.find_incremental_base",
           return_value=None)
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.get_latest_guid", side_effect=[1, 1])
    @patch("pilo.context.DatasetMapping")
    def test_diverged_precedes_behind(self, Mapping, *_):

        mapping = Mapping.return_value
        mapping.inverse.return_value = "tank/a"
        status, msg = repl.replication_state("tank/a", "backup/a")

        self.assertEqual(status, repl.ReplicationStatus.DIVERGED)

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.back.replication.find_incremental_base",
           return_value="tank/a@t0")
    @patch("pilo.zfs.get_latest_guid")
    @patch("pilo.zfs.list_filesystems")
    @patch("pilo.context.DatasetMapping")
    def test_checks_replica_child_filesystems(
        self,
        Mapping,
        list_fs,
        guid,
        *_
    ):
        guid.side_effect = [
            1, 1,
            1, 1,
            2, 3
        ]
        list_fs.return_value = [
            "backup/a",
            "backup/a/child",
        ]
        mapping = Mapping.return_value
        mapping.inverse.side_effect = [
            "tank/a",
            "tank/a/child",
        ]

        repl.replication_state("tank/a", "backup/a")

        self.assertEqual(list_fs.call_count, 1)
        self.assertEqual(mapping.inverse.call_count, 2)

    @patch("pilo.context.DatasetMapping")
    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.list_filesystems")
    @patch("pilo.zfs.get_latest_guid")
    @patch("pilo.back.replication.find_incremental_base",
           return_value="tank/a@t0")
    def test_missing_replica_child_is_behind(
        self,
        _base,
        guid,
        list_fs,
        exists,
        mapping_cls,
    ):

        guid.side_effect = [
            1, 1,
            1, 1,
            2, 3
        ]
        list_fs.side_effect = [
            ["backup/a"],
            ["tank/a", "tank/a/child"],
        ]

        mapping = mapping_cls.return_value
        mapping.inverse.return_value = "tank/a"
        mapping.map.side_effect = [
            "backup/a",
            "backup/a/child",
        ]

        exists.side_effect = [
            True,   # source exists for backup/a
            True,   # backup/a exists
            False,  # backup/a/child missing
        ]

        status, msg = repl.replication_state(
            "tank/a",
            "backup/a",
        )

        self.assertEqual(status, repl.ReplicationStatus.BEHIND)
        self.assertEqual(msg, "missing backup/a/child")

    @patch("pilo.context.DatasetMapping")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.list_filesystems")
    @patch("pilo.back.replication.find_incremental_base",
           return_value="tank/a@t0")
    @patch("pilo.zfs.get_latest_guid")
    def test_synchronized(
        self,
        guid,
        _base,
        list_fs,
        _exists,
        mapping_cls,
    ):

        guid.side_effect = [
            1, 1,   # root
            1, 1,   # child compare
        ]

        list_fs.side_effect = [
            ["backup/a"],
            ["tank/a"],
        ]

        mapping = mapping_cls.return_value
        mapping.inverse.return_value = "tank/a"
        mapping.map.return_value = "backup/a"

        status, msg = repl.replication_state(
            "tank/a",
            "backup/a",
        )

        self.assertEqual(status, repl.ReplicationStatus.OK)
        self.assertIsNone(msg)

    @patch("pilo.zfs.get_latest_guid", return_value=3)
    @patch("pilo.zfs.snapshot_guids")
    def test_incremental_base_allows_pruned_older_snapshots(
        self,
        guids,
        *_
    ):

        guids.return_value = [
            ["tank/a@t3", 3],
        ]

        base = repl.find_incremental_base(
            "tank/a",
            "backup/a",
        )

        self.assertEqual(base, "tank/a@t3")

    @patch("pilo.context.DatasetMapping")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.list_filesystems")
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.get_latest_guid")
    def test_ok_after_full_traversal(
        self,
        guid,
        base,
        list_fs,
        _exists,
        mapping_cls,
    ):

        guid.side_effect = [
            1, 1,
            1, 1,
            2, 2,
        ]

        base.side_effect = [
            "tank/a@t1",
            "tank/a/child@t1",
        ]

        list_fs.side_effect = [
            ["backup/a", "backup/a/child"],
            ["tank/a", "tank/a/child"],
        ]

        mapping = mapping_cls.return_value
        mapping.inverse.side_effect = [
            "tank/a",
            "tank/a/child",
        ]

        mapping.map.side_effect = [
            "backup/a",
            "backup/a/child",
        ]

        status, msg = repl.replication_state(
            "tank/a",
            "backup/a",
        )

        self.assertEqual(status, repl.ReplicationStatus.OK)
        self.assertIsNone(msg)

    @patch("pilo.context.DatasetMapping")
    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.list_filesystems")
    @patch("pilo.back.replication.find_incremental_base")
    @patch("pilo.zfs.get_latest_guid")
    def test_replica_old_history_allowed(
        self,
        guid,
        base,
        list_fs,
        _exists,
        mapping_cls,
    ):

        guid.side_effect = [
            3, 2,
            3, 2,
        ]

        list_fs.side_effect = [
            ["backup/a"],
            ["tank/a"],
        ]

        base.return_value = "tank/a@t2"

        mapping = mapping_cls.return_value
        mapping.inverse.return_value = "tank/a"
        mapping.map.return_value = "backup/a"

        status, msg = repl.replication_state(
            "tank/a",
            "backup/a",
        )

        self.assertEqual(
            status,
            repl.ReplicationStatus.BEHIND,
        )

    @patch("pilo.zfs.list_filesystems")
    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.get_latest_guid")
    @patch("pilo.context.DatasetMapping")
    @patch("pilo.back.replication.find_incremental_base")
    def test_replica_only_dataset_is_ignored(
        self,
        base,
        mapping_cls,
        guid,
        exists,
        list_fs,
    ):

        guid.side_effect = [
            1, 1,  # initial sanity checks
            1, 1,  # backup/a comparison
        ]

        list_fs.side_effect = [
            ["backup/a", "backup/a/orphan"],
            ["tank/a"],
        ]

        mapping = mapping_cls.return_value

        mapping.inverse.side_effect = [
            "tank/a",
            "tank/a/orphan",
        ]

        mapping.map.return_value = "backup/a"

        exists.side_effect = [
            True,   # tank/a exists
            False,  # tank/a/orphan absent on source
            True,   # backup/a exists
        ]

        base.return_value = "tank/a@t0"

        status, msg = repl.replication_state(
            "tank/a",
            "backup/a",
        )

        self.assertEqual(
            status,
            repl.ReplicationStatus.OK,
        )

        self.assertIsNone(msg)
