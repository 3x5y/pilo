import unittest
from unittest.mock import patch

import pilo
import pilotest


class TestRecoveryPlan(unittest.TestCase):

    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.latest_snapshot")
    def test_build_plan_root(self, mock_latest, mock_exists, *_):
        mock_latest.return_value = "backup/a@r-123"

        def side_effect(ds):
            # replica exists, target does NOT
            if ds == "backup/a":
                return True
            if ds == "tank/a":
                return False
            return False
        mock_exists.side_effect = side_effect
        cx = pilotest.make_context()

        plan = pilo.build_recovery_plan(cx, "tank/a")

        self.assertEqual(plan.target, "tank/a")
        self.assertEqual(plan.replica, "backup/a")
        self.assertEqual(plan.snapshot, "backup/a@r-123")
        self.assertTrue(plan.recursive)

    @patch("pilo.zfs.dataset_exists", return_value=False)
    def test_build_plan_requires_replica(self, _):
        cx = pilotest.make_context()

        with pilotest.assert_fatal(self):
            pilo.build_recovery_plan(cx, "tank/a")

    @patch("pilo.zfs.dataset_exists", return_value=True)
    @patch("pilo.zfs.latest_snapshot", return_value="wrong@foo")
    def test_snapshot_must_match_replica(self, mock_snap, _):
        cx = pilotest.make_context()

        with pilotest.assert_fatal(self):
            pilo.build_recovery_plan(cx, "tank/a")


    @patch("pilo.zfs.snapshot_exists", return_value=True)
    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.latest_snapshot")
    def test_build_plan_subdataset(self, mock_latest, mock_exists, *_):
        mock_latest.return_value = "backup/a/foo@r-1"

        def side_effect(ds):
            # replica exists, target does NOT
            if ds == "backup/a/foo":
                return True
            if ds == "tank/a/foo":
                return False
            return False
        mock_exists.side_effect = side_effect

        cx = pilotest.make_context()

        plan = pilo.build_recovery_plan(cx, "tank/a/foo")

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
            pilo.build_recovery_plan(cx, "tank/a")

    @patch("pilo.apply_ownership")
    @patch("pilo.subprocess.run")
    @patch("pilo.apply_dataset_contract")
    @patch("pilo.restore_dataset")
    def test_execute_plan(self, mock_restore, mock_contract, mock_run,
                          mock_owner):
        plan = pilo.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        cx = pilotest.make_context()
        pilo.execute_recovery_plan(plan, cx)

        mock_restore.assert_called_once_with(
            "backup/a@r-1",
            "tank/a",
            recursive=True,
        )

    @patch("pilo.apply_ownership")
    @patch("pilo.subprocess.run")
    @patch("pilo.apply_dataset_contract")
    @patch("pilo.restore_dataset")
    def test_execute_plan_applies_contract(self, mock_restore, mock_contract,
                                           mock_owner, mock_run):
        cx = pilotest.make_context()

        plan = pilo.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        pilo.execute_recovery_plan(plan, cx)

        mock_restore.assert_called_once()
        mock_contract.assert_called_once_with(cx)

    @patch("pilo.apply_ownership")
    @patch("pilo.subprocess.run")
    @patch("pilo.apply_dataset_contract")
    @patch("pilo.restore_dataset")
    def test_execute_plan_mounts_datasets(self, mock_restore, mock_contract,
                                          mock_run, mock_owner):
        cx = pilotest.make_context()

        plan = pilo.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        pilo.execute_recovery_plan(plan, cx)

        #mock_run.assert_called_with(["zfs", "mount", "-a"], check=True)
        mock_run.assert_any_call(["zfs", "mount", "-a"], check=True)

    @patch("pilo.apply_ownership")
    @patch("pilo.ensure_runtime_dirs")
    @patch("pilo.subprocess.run")
    @patch("pilo.apply_dataset_contract")
    @patch("pilo.restore_dataset")
    def test_execute_plan_ensures_runtime_dirs(
        self, mock_restore, mock_contract, mock_run, mock_dirs,
        mock_owner,
    ):
        cx = pilotest.make_context()

        plan = pilo.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        pilo.execute_recovery_plan(plan, cx)

        mock_dirs.assert_called_once_with(cx)

    @patch("pilo.apply_ownership")
    @patch("pilo.ensure_runtime_dirs")
    @patch("pilo.subprocess.run")
    @patch("pilo.apply_dataset_contract")
    @patch("pilo.restore_dataset")
    def test_execute_plan_applies_ownership(
        self, mock_restore, mock_contract, mock_run, mock_dirs, mock_owner
    ):
        cx = pilotest.make_context()

        plan = pilo.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        pilo.execute_recovery_plan(plan, cx)

        mock_owner.assert_called_once_with(cx)

    @patch("pilo.execute_recovery_plan")
    @patch("pilo.build_recovery_plan")
    def test_recover_uses_plan(self, mock_build, mock_exec):
        cx = pilotest.make_context()
        mock_build.return_value = pilo.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        with pilotest.suppress_stdout():
            with patch("pilo.Context", return_value=cx):
                with patch.object(cx, "args", ["tank/a"]):
                    mod = pilotest.import_command('recover')
                    mod.main()

        mock_build.assert_called_once_with(cx, "tank/a")
        mock_exec.assert_called_once()
