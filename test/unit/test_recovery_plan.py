import importlib
import unittest
from pathlib import Path
from unittest.mock import patch
import pilo


def import_command(name):
    modname = f'pilo-{name}'
    filename = modname + '.py'
    modpath = Path(pilo.__file__).parent / filename
    spec = importlib.util.spec_from_file_location(modname, modpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_context():
    return pilo.Context(environ={
        "PILO_ROOT": "tank/a",
        "PILO_REPLICA_ROOT": "backup/a",
        "PILO_ADMIN_DATASET": "tank/a/admin",
        "PILO_INTAKE_DATASET": "tank/a/intake",
        "PILO_PILE_DATASET": "tank/a/pile",
        "PILO_STATIC_DATASET": "tank/a/static",
        "PILO_PATH": "/tmp",
        "PILO_ADMIN_PATH": "/tmp/admin",
        "PILO_INTAKE_PATH": "/tmp/intake",
        "PILO_PILE_PATH": "/tmp/pile",
        "PILO_STATIC_PATH": "/tmp/static",
        "PILO_USER": "root",
    })


class TestRecoveryPlan(unittest.TestCase):

    #@patch("pilo.dataset_exists", return_value=True)
    @patch("pilo.dataset_exists")
    @patch("pilo.zfs_latest_snapshot")
    def test_build_plan_root(self, mock_latest, mock_exists):
        mock_latest.return_value = "backup/a@r-123"

        def side_effect(ds):
            # replica exists, target does NOT
            if ds == "backup/a":
                return True
            if ds == "tank/a":
                return False
            return False
        mock_exists.side_effect = side_effect
        cx = make_context()

        plan = pilo.build_recovery_plan(cx, "tank/a")

        self.assertEqual(plan.target, "tank/a")
        self.assertEqual(plan.replica, "backup/a")
        self.assertEqual(plan.snapshot, "backup/a@r-123")
        self.assertTrue(plan.recursive)

    @patch("pilo.dataset_exists", return_value=False)
    def test_build_plan_requires_replica(self, _):
        cx = make_context()

        with self.assertRaises(SystemExit):
            pilo.build_recovery_plan(cx, "tank/a")

    @patch("pilo.dataset_exists", return_value=True)
    @patch("pilo.zfs_latest_snapshot", return_value="wrong@foo")
    def test_snapshot_must_match_replica(self, mock_snap, _):
        cx = make_context()

        with self.assertRaises(SystemExit):
            pilo.build_recovery_plan(cx, "tank/a")

    @patch("pilo.dataset_exists")
    @patch("pilo.zfs_latest_snapshot")
    def test_build_plan_subdataset(self, mock_latest, mock_exists):
        mock_latest.return_value = "backup/a/foo@r-1"

        def side_effect(ds):
            # replica exists, target does NOT
            if ds == "backup/a/foo":
                return True
            if ds == "tank/a/foo":
                return False
            return False
        mock_exists.side_effect = side_effect

        cx = make_context()

        plan = pilo.build_recovery_plan(cx, "tank/a/foo")

        self.assertEqual(plan.replica, "backup/a/foo")
        self.assertEqual(plan.snapshot, "backup/a/foo@r-1")

    @patch("pilo.dataset_exists")
    @patch("pilo.zfs_latest_snapshot", return_value="backup/a@r-1")
    def test_plan_requires_new_target(self, mock_snap, mock_exists):
        # target exists
        def side_effect(ds):
            return ds == "tank/a"
        mock_exists.side_effect = side_effect

        cx = make_context()

        with self.assertRaises(SystemExit):
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

        cx = make_context()
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
        cx = make_context()

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
        cx = make_context()

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
        cx = make_context()

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
        cx = make_context()

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
        cx = make_context()
        mock_build.return_value = pilo.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        with patch("pilo.Context", return_value=cx):
            with patch.object(cx, "args", ["tank/a"]):
                mod = import_command('recover')
                mod.main()

        mock_build.assert_called_once_with(cx, "tank/a")
        mock_exec.assert_called_once()
