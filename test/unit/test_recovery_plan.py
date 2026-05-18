import unittest
from unittest.mock import patch

from pilo import state
from pilo.back import recover
import pilotest


class TestRecoveryPlan(pilotest.TestCase):

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.latest_snapshot")
    def test_build_plan_root(self, mock_latest, mock_exists, *_):
        mock_latest.return_value = "backup/a@r-123"
        mock_exists.side_effect = lambda ds: ds in ("backup", "backup/a")
        cx = pilotest.make_context()

        plan = recover.build_recovery_plan(cx, "tank/a")

        self.assertEqual(plan.target, "tank/a")
        self.assertEqual(plan.replica, "backup/a")
        self.assertEqual(plan.snapshot, "backup/a@r-123")
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

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.latest_snapshot")
    def test_build_plan_subdataset(self, mock_latest, mock_exists, *_):
        mock_latest.return_value = "backup/a/foo@r-1"
        mock_exists.side_effect = lambda ds: ds in ("backup", "backup/a/foo")

        cx = pilotest.make_context()

        plan = recover.build_recovery_plan(cx, "tank/a/foo")

        self.assertEqual(plan.replica, "backup/a/foo")
        self.assertEqual(plan.snapshot, "backup/a/foo@r-1")

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

    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("pilo.normalize.apply_ownership")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contracts")
    @patch("pilo.back.restore.restore_dataset")
    def test_execute_plan(self, mock_restore, mock_contract, mock_run,
                          mock_owner, mock_dirs):
        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        cx = pilotest.make_context()
        recover.execute_recovery_plan(plan, cx)

        mock_restore.assert_called_once_with(
            "backup/a@r-1",
            "tank/a",
            recursive=True,
        )

    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("pilo.normalize.apply_ownership")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contracts")
    @patch("pilo.back.restore.restore_dataset")
    def test_execute_plan_applies_contract(self, mock_restore, mock_contract,
                                           mock_owner, mock_run, mock_dirs):
        cx = pilotest.make_context()

        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        recover.execute_recovery_plan(plan, cx)

        mock_restore.assert_called_once()
        mock_contract.assert_called_once_with(cx)

    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.zfs.run")
    @patch("pilo.normalize.apply_dataset_contracts")
    @patch("pilo.back.restore.restore_dataset")
    def test_execute_plan_mounts_datasets(self, mock_restore, mock_contract,
                                          mock_run, mock_owner, mock_dirs):
        cx = pilotest.make_context()

        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        recover.execute_recovery_plan(plan, cx)

        mock_run.assert_called_with(["zfs", "mount", "-a"])

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contracts")
    @patch("pilo.back.restore.restore_dataset")
    def test_execute_plan_ensures_runtime_dirs(
        self, mock_restore, mock_contract, mock_run, mock_dirs,
        mock_owner,
    ):
        cx = pilotest.make_context()

        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        recover.execute_recovery_plan(plan, cx)

        mock_dirs.assert_called_once_with(cx)

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contracts")
    @patch("pilo.back.restore.restore_dataset")
    def test_execute_plan_applies_ownership(
        self, mock_restore, mock_contract, mock_run, mock_dirs, mock_owner
    ):
        cx = pilotest.make_context()

        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        recover.execute_recovery_plan(plan, cx)

        mock_owner.assert_called_once_with(cx)

    @patch("pilo.back.recover.execute_recovery_plan")
    @patch("pilo.back.recover.build_recovery_plan")
    def test_recover_uses_plan(self, mock_build, mock_exec):
        cx = pilotest.make_context()
        cx.args = ["tank/a"]
        mock_build.return_value = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        mod = pilotest.import_command('recover')

        with pilotest.suppress_stdout():
            with patch("pilo.context.Context", return_value=cx):
                mod.main()

        mock_build.assert_called_once_with(cx, "tank/a")
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
    @patch("pilo.state.detect_lifecycle")
    def test_build_plan_uses_detected_secondary(
        self,
        mock_detect,
        mock_latest,
        mock_exists,
        *_,
    ):
        mock_detect.return_value = state.LifecycleStatus(
            state=state.LifecycleState.NORMAL,
            secondary="backup/a",
        )

        mock_latest.return_value = "backup/a@r-1"

        def side_effect(ds):
            return ds == "backup/a"

        mock_exists.side_effect = side_effect

        cx = pilotest.make_context()

        plan = recover.build_recovery_plan(cx, "tank/a")

        self.assertEqual(plan.replica, "backup/a")
