import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pilo.storage import lifecycle
from pilo.storage import recover
from pilo.storage import replay
import pilotest


class TestRecoveryPlan(pilotest.TestCase):

    @patch("pilo.storage.lifecycle.lifecycle_recoverable", return_value=True)
    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.latest_snapshot", return_value="backup/a@r-123")
    @patch("pilo.storage.lifecycle.detect_lifecycle")
    @patch("pilo.zfs.dataset_exists")
    def test_build_plan_root(self, exists, detect, *_):

        detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
            secondary="backup/a",
        )
        exists.side_effect = lambda ds: ds == "backup/a"

        cx = pilotest.make_context()

        plan = recover.build_recovery_plan(cx, "tank/a")

        self.assertEqual(plan.target, "tank/a")
        self.assertEqual(plan.replica, "backup/a")
        self.assertEqual(plan.baseline_snapshot, "backup/a@r-123")
        self.assertTrue(plan.recursive)

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_build_plan_requires_replica(self, _):
        cx = pilotest.make_context()

        with pilotest.assert_fatal(self):
            recover.build_recovery_plan(cx, "tank/a")

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.latest_snapshot", return_value="wrong@foo")
    def test_snapshot_must_match_replica(self, mock_snap, _):
        cx = pilotest.make_context()

        with pilotest.assert_fatal(self):
            recover.build_recovery_plan(cx, "tank/a")

    @patch("pilo.storage.lifecycle.lifecycle_recoverable", return_value=True)
    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.latest_snapshot", return_value="backup/a/foo@r-1")
    @patch("pilo.storage.lifecycle.detect_lifecycle")
    @patch("pilo.zfs.dataset_exists")
    def test_build_plan_subdataset(self, exists, detect, *_):

        detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
            secondary="backup/a",
        )
        exists.side_effect = lambda ds: ds == "backup/a/foo"

        cx = pilotest.make_context()

        plan = recover.build_recovery_plan(cx, "tank/a/foo")

        self.assertEqual(plan.replica, "backup/a/foo")
        self.assertEqual(plan.baseline_snapshot, "backup/a/foo@r-1")

    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.latest_snapshot", return_value="backup/a@r-1")
    def test_plan_requires_new_target(self, mock_snap, mock_exists):
        # target exists
        def side_effect(ds):
            return ds == "tank/a"
        mock_exists.side_effect = side_effect

        cx = pilotest.make_context()

        with pilotest.assert_fatal(self):
            recover.build_recovery_plan(cx, "tank/a")

    @patch("pilo.storage.normalize.ensure_runtime_dirs")
    @patch("pilo.storage.normalize.apply_ownership")
    @patch("subprocess.run")
    @patch("pilo.storage.normalize.apply_dataset_contracts")
    @patch("pilo.storage.restore.restore_dataset")
    @patch("builtins.print")
    def test_execute_plan(self, mock_print, mock_restore, mock_contract,
                          mock_run, mock_owner, mock_dirs):
        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
        )

        cx = pilotest.make_context()
        recover.execute_recovery_plan(plan, cx)

        mock_restore.assert_called_once_with(
            "backup/a@r-1",
            "tank/a",
            recursive=True,
        )

    @patch("pilo.storage.normalize.ensure_runtime_dirs")
    @patch("pilo.storage.normalize.apply_ownership")
    @patch("subprocess.run")
    @patch("pilo.storage.normalize.apply_dataset_contracts")
    @patch("pilo.storage.restore.restore_dataset")
    @patch("builtins.print")
    def test_execute_plan_applies_contract(self, mock_print, mock_restore,
                                           mock_contract, mock_owner, mock_run,
                                           mock_dirs):
        cx = pilotest.make_context()

        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
        )

        recover.execute_recovery_plan(plan, cx)

        mock_restore.assert_called_once()
        mock_contract.assert_called_once_with(cx)

    @patch("pilo.storage.normalize.ensure_runtime_dirs")
    @patch("pilo.storage.normalize.apply_ownership")
    @patch("pilo.zfs.run")
    @patch("pilo.storage.normalize.apply_dataset_contracts")
    @patch("pilo.storage.restore.restore_dataset")
    @patch("builtins.print")
    def test_execute_plan_mounts_datasets(self, mock_print, mock_restore,
                                          mock_contract, mock_run, mock_owner,
                                          mock_dirs):
        cx = pilotest.make_context()

        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
        )

        recover.execute_recovery_plan(plan, cx)

        mock_run.assert_called_with(["zfs", "mount", "-a"])

    @patch("pilo.storage.normalize.apply_ownership")
    @patch("pilo.storage.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.storage.normalize.apply_dataset_contracts")
    @patch("pilo.storage.restore.restore_dataset")
    @patch("builtins.print")
    def test_execute_plan_ensures_runtime_dirs(
        self, mock_print, mock_restore, mock_contract, mock_run, mock_dirs,
        mock_owner,
    ):
        cx = pilotest.make_context()

        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
        )

        recover.execute_recovery_plan(plan, cx)

        mock_dirs.assert_called_once_with(cx)

    @patch("pilo.storage.normalize.apply_ownership")
    @patch("pilo.storage.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.storage.normalize.apply_dataset_contracts")
    @patch("pilo.storage.restore.restore_dataset")
    @patch("builtins.print")
    def test_execute_plan_applies_ownership(
        self, mock_print, mock_restore, mock_contract, mock_run, mock_dirs,
        mock_owner
    ):
        cx = pilotest.make_context()

        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
        )

        recover.execute_recovery_plan(plan, cx)

        mock_owner.assert_called_once_with(cx)

    @patch("pilo.storage.recover.execute_recovery_plan")
    @patch("pilo.storage.recover.build_recovery_plan")
    def test_recover_uses_plan(self, mock_build, mock_exec):
        cx = pilotest.make_context()
        cx.args = ["tank/a"]
        mock_build.return_value = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
        )

        mod = pilotest.import_command('storage-recover')

        with pilotest.suppress_stdout():
            with patch("pilo.context.Context", return_value=cx):
                mod.main()

        mock_build.assert_called_once_with(cx, "tank/a", stream_dir=None)
        mock_exec.assert_called_once()

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.latest_snapshot", return_value="backup/a@r1")
    def test_build_plan_uses_validation(self, *_):
        cx = pilotest.make_context()

        with pilotest.assert_fatal(self):
            recover.build_recovery_plan(cx, "invalid/root")

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.latest_snapshot")
    @patch("pilo.storage.lifecycle.detect_lifecycle")
    def test_build_plan_uses_detected_secondary(
        self,
        mock_detect,
        mock_latest,
        mock_exists,
        *_,
    ):
        mock_detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
            secondary="backup/a",
        )

        mock_latest.return_value = "backup/a@r-1"

        def side_effect(ds):
            return ds == "backup/a"

        mock_exists.side_effect = side_effect

        cx = pilotest.make_context()

        plan = recover.build_recovery_plan(cx, "tank/a")

        self.assertEqual(plan.replica, "backup/a")


class TestReplayCatchupPlan(pilotest.TestCase):

    def test_fields(self):
        batch = replay.BatchReplayPlan(plans=())
        plan = recover.ReplayCatchupPlan(
            replay_batch=batch, latest_snapshot="s1")
        self.assertIs(plan.replay_batch, batch)
        self.assertEqual(plan.latest_snapshot, "s1")

    def test_no_latest(self):
        batch = replay.BatchReplayPlan(plans=())
        plan = recover.ReplayCatchupPlan(
            replay_batch=batch, latest_snapshot=None)
        self.assertIsNone(plan.latest_snapshot)

    def test_frozen(self):
        batch = replay.BatchReplayPlan(plans=())
        plan = recover.ReplayCatchupPlan(
            replay_batch=batch, latest_snapshot=None)
        with self.assertRaises(AttributeError):
            plan.latest_snapshot = "other"

    def test_frozen_batch(self):
        batch = replay.BatchReplayPlan(plans=())
        plan = recover.ReplayCatchupPlan(
            replay_batch=batch, latest_snapshot=None)
        with self.assertRaises(AttributeError):
            plan.replay_batch = None


class TestRecoveryPlanCatchup(pilotest.TestCase):

    def test_defaults_none(self):
        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
        )
        self.assertIsNone(plan.catchup)

    def test_with_catchup(self):
        batch = replay.BatchReplayPlan(plans=())
        catchup = recover.ReplayCatchupPlan(
            replay_batch=batch, latest_snapshot="s2")
        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
            catchup=catchup,
        )
        self.assertIs(plan.catchup, catchup)
        self.assertIs(plan.catchup.replay_batch, batch)
        self.assertEqual(plan.catchup.latest_snapshot, "s2")


class TestBuildRecoveryReplayPlan(pilotest.TestCase):

    @patch("pilo.storage.recover.replay.find_streams", return_value=[])
    def test_empty_dir(self, mock_find):
        result = recover.build_recovery_replay_plan(
            "/streams", "tank/a", "baseline_snap")
        self.assertIsNone(result)

    @patch("pilo.storage.recover.replay.filter_newer_than", return_value=[])
    @patch("pilo.storage.recover.replay.order_streams")
    @patch("pilo.storage.recover.replay.find_streams")
    def test_all_filtered(self, mock_find, mock_order, mock_filter):
        mock_find.return_value = [Path("/s1.zfs")]
        mock_order.return_value = [Path("/s1.zfs")]
        result = recover.build_recovery_replay_plan(
            "/streams", "tank/a", "baseline_snap")
        self.assertIsNone(result)

    @patch("pilo.storage.recover.replay.build_batch_replay_plan")
    @patch("pilo.storage.recover.replay.filter_newer_than")
    @patch("pilo.storage.recover.replay.order_streams")
    @patch("pilo.storage.recover.replay.find_streams")
    def test_happy_path(self, mock_find, mock_order, mock_filter,
                        mock_build_batch):
        mock_find.return_value = [Path("/s1.zfs"), Path("/s2.zfs")]
        mock_order.return_value = [Path("/s1.zfs"), Path("/s2.zfs")]
        mock_filter.return_value = [Path("/s2.zfs")]
        batch = replay.BatchReplayPlan(plans=(
            replay.ReplayPlan(
                stream_path=Path("/s2.zfs"),
                manifest=SimpleNamespace(snapshot="s2"),
                target_dataset="tank/a",
            ),
        ))
        mock_build_batch.return_value = batch

        result = recover.build_recovery_replay_plan(
            "/streams", "tank/a", "baseline_snap")

        self.assertIsNotNone(result)
        self.assertIs(result.replay_batch, batch)

    @patch("pilo.storage.recover.replay.build_batch_replay_plan")
    @patch("pilo.storage.recover.replay.filter_newer_than")
    @patch("pilo.storage.recover.replay.order_streams")
    @patch("pilo.storage.recover.replay.find_streams")
    def test_latest_snapshot(self, mock_find, mock_order, mock_filter,
                             mock_build_batch):
        mock_find.return_value = [Path("/s1.zfs"), Path("/s2.zfs")]
        mock_order.return_value = [Path("/s1.zfs"), Path("/s2.zfs")]
        mock_filter.return_value = [Path("/s1.zfs"), Path("/s2.zfs")]
        batch = replay.BatchReplayPlan(plans=(
            replay.ReplayPlan(
                stream_path=Path("/s1.zfs"),
                manifest=SimpleNamespace(
                    snapshot="20260522_010000_000000-reg"),
                target_dataset="tank/a",
            ),
            replay.ReplayPlan(
                stream_path=Path("/s2.zfs"),
                manifest=SimpleNamespace(
                    snapshot="20260522_020000_000000-reg"),
                target_dataset="tank/a",
            ),
        ))
        mock_build_batch.return_value = batch

        result = recover.build_recovery_replay_plan(
            "/streams", "tank/a", "20260522_000000_000000-reg")

        self.assertEqual(result.latest_snapshot,
                         "20260522_020000_000000-reg")

    @patch("pilo.storage.recover.replay.build_batch_replay_plan")
    @patch("pilo.storage.recover.replay.filter_newer_than")
    @patch("pilo.storage.recover.replay.order_streams")
    @patch("pilo.storage.recover.replay.find_streams")
    def test_latest_snapshot_single_stream(
        self, mock_find, mock_order, mock_filter, mock_build_batch
    ):
        mock_find.return_value = [Path("/s1.zfs")]
        mock_order.return_value = [Path("/s1.zfs")]
        mock_filter.return_value = [Path("/s1.zfs")]
        batch = replay.BatchReplayPlan(plans=(
            replay.ReplayPlan(
                stream_path=Path("/s1.zfs"),
                manifest=SimpleNamespace(
                    snapshot="20260522_010000_000000-reg"),
                target_dataset="tank/a",
            ),
        ))
        mock_build_batch.return_value = batch

        result = recover.build_recovery_replay_plan(
            "/streams", "tank/a", "20260522_000000_000000-reg")

        self.assertEqual(result.latest_snapshot,
                         "20260522_010000_000000-reg")

    @patch("pilo.storage.recover.build_recovery_replay_plan")
    @patch("pilo.storage.lifecycle.lifecycle_recoverable", return_value=True)
    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.latest_snapshot", return_value="backup/a@r-1")
    @patch("pilo.storage.lifecycle.detect_lifecycle")
    @patch("pilo.zfs.dataset_exists")
    def test_build_plan_with_stream_dir_calls_replay_plan(
        self, mock_exists, mock_detect, *_,
    ):
        mock_detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
            secondary="backup/a",
        )
        mock_exists.side_effect = lambda ds: ds == "backup/a"

        cx = pilotest.make_context()
        plan = recover.build_recovery_plan(
            cx, "tank/a", stream_dir="/streams")

        self.assertIsNotNone(plan.catchup)

    @patch("pilo.storage.lifecycle.lifecycle_recoverable", return_value=True)
    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.latest_snapshot", return_value="backup/a@r-1")
    @patch("pilo.storage.lifecycle.detect_lifecycle")
    @patch("pilo.zfs.dataset_exists")
    def test_build_plan_no_stream_dir_no_catchup(
        self, mock_exists, mock_detect, *_,
    ):
        mock_detect.return_value = lifecycle.LifecycleStatus(
            state=lifecycle.LifecycleState.NORMAL,
            secondary="backup/a",
        )
        mock_exists.side_effect = lambda ds: ds == "backup/a"

        cx = pilotest.make_context()
        plan = recover.build_recovery_plan(cx, "tank/a")

        self.assertIsNone(plan.catchup)

    @patch("pilo.storage.recover.replay.execute_batch_replay_plan")
    @patch("builtins.print")
    def test_execute_with_catchup(self, mock_print, mock_replay):
        batch = replay.BatchReplayPlan(plans=())
        catchup = recover.ReplayCatchupPlan(
            replay_batch=batch, latest_snapshot="s2")
        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
            catchup=catchup,
        )
        cx = pilotest.make_context()
        with patch("pilo.storage.restore.restore_dataset"):
            with patch("pilo.storage.normalize.normalize_system"):
                recover.execute_recovery_plan(plan, cx)

        mock_replay.assert_called_once_with(batch)
        mock_print.assert_any_call("RESTORE backup/a@r-1")
        mock_print.assert_any_call("REPLAY 0 streams")
        mock_print.assert_any_call("NORMALIZE")

    @patch("builtins.print")
    def test_execute_no_catchup(self, mock_print):
        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
        )
        cx = pilotest.make_context()
        with patch("pilo.storage.restore.restore_dataset"):
            with patch("pilo.storage.normalize.normalize_system"):
                with patch(
                    "pilo.storage.recover.replay.execute_batch_replay_plan"
                ) as mock_replay:
                    recover.execute_recovery_plan(plan, cx)

        mock_replay.assert_not_called()
        mock_print.assert_any_call("RESTORE backup/a@r-1")
        mock_print.assert_any_call("NORMALIZE")
        replay_calls = [c for c in mock_print.call_args_list
                        if c[0][0].startswith("REPLAY")]
        self.assertEqual(len(replay_calls), 0)

    @patch("pilo.storage.recover.replay.execute_batch_replay_plan")
    @patch("builtins.print")
    def test_execute_reports_replay_results(
        self, mock_print, mock_replay,
    ):
        r1 = replay.ReplayResult(
            status="APPLIED", stream="s1", snapshot="snap1",
            source="src", target_dataset="tank/a",
            applied_at="2026-01-01T00:00:00",
        )
        r2 = replay.ReplayResult(
            status="SKIPPED", stream="s2", snapshot="snap2",
            source="src", target_dataset="tank/a",
            applied_at="2026-01-01T00:00:00",
        )
        mock_replay.return_value = [r1, r2]

        batch = replay.BatchReplayPlan(plans=(
            replay.ReplayPlan(
                stream_path=Path("/s1.zfs"),
                manifest=SimpleNamespace(
                    stream="s1", snapshot="snap1", source="src",
                    guid="g1", checksum="c1",
                ),
                target_dataset="tank/a",
            ),
            replay.ReplayPlan(
                stream_path=Path("/s2.zfs"),
                manifest=SimpleNamespace(
                    stream="s2", snapshot="snap2", source="src",
                    guid="g2", checksum="c2",
                ),
                target_dataset="tank/a",
            ),
        ))
        catchup = recover.ReplayCatchupPlan(
            replay_batch=batch, latest_snapshot="snap2")
        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
            catchup=catchup,
        )
        cx = pilotest.make_context()
        with patch("pilo.storage.restore.restore_dataset"):
            with patch("pilo.storage.normalize.normalize_system"):
                recover.execute_recovery_plan(plan, cx)

        mock_print.assert_any_call("APPLIED snap1")
        mock_print.assert_any_call("SKIPPED snap2")

    @patch("pilo.storage.recover.replay.execute_batch_replay_plan")
    @patch("builtins.print")
    def test_execute_phases_in_order(
        self, mock_print, mock_replay,
    ):
        mock_replay.return_value = []
        batch = replay.BatchReplayPlan(plans=())
        catchup = recover.ReplayCatchupPlan(
            replay_batch=batch, latest_snapshot="snap1")
        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            baseline_snapshot="backup/a@r-1",
            recursive=True,
            catchup=catchup,
        )
        cx = pilotest.make_context()
        with patch("pilo.storage.restore.restore_dataset"):
            with patch("pilo.storage.normalize.normalize_system"):
                recover.execute_recovery_plan(plan, cx)

        calls = [c[0][0] for c in mock_print.call_args_list]
        restore_idx = calls.index("RESTORE backup/a@r-1")
        replay_idx = calls.index("REPLAY 0 streams")
        normalize_idx = calls.index("NORMALIZE")
        self.assertLess(restore_idx, replay_idx)
        self.assertLess(replay_idx, normalize_idx)
