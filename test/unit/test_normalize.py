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


class TestNormalize(unittest.TestCase):

    @patch("pilo.apply_ownership")
    @patch("pilo.ensure_runtime_dirs")
    @patch("pilo.subprocess.run")
    @patch("pilo.apply_dataset_contract")
    def test_normalize_applies_contract(self, mock_contract, mock_run,
                                        mock_dirs, mock_owner):

        cx = make_context()
        pilo.normalize_system(cx)
        mock_contract.assert_called_once_with(cx)

    @patch("pilo.apply_ownership")
    @patch("pilo.ensure_runtime_dirs")
    @patch("pilo.subprocess.run")
    @patch("pilo.apply_dataset_contract")
    def test_normalize_mounts(self, mock_contract, mock_run, mock_dirs,
                              mock_owner):

        cx = make_context()
        pilo.normalize_system(cx)
        mock_run.assert_called_once_with(["zfs", "mount", "-a"], check=True)

    @patch("pilo.apply_ownership")
    @patch("pilo.ensure_runtime_dirs")
    @patch("pilo.subprocess.run")
    @patch("pilo.apply_dataset_contract")
    def _test_normalize_ensures_runtime_dirs(
        self, mock_contract, mock_run, mock_dirs, mock_owner
    ):

        cx = make_context()
        pilo.normalize_system(cx)
        mock_dirs.assert_called_once_with(cx)

    @patch("pilo.apply_ownership")
    @patch("pilo.ensure_runtime_dirs")
    @patch("pilo.subprocess.run")
    @patch("pilo.apply_dataset_contract")
    def test_normalize_applies_ownership(
        self, mock_contract, mock_run, mock_dirs, mock_owner
    ):
        cx = make_context()

        pilo.normalize_system(cx)

        mock_owner.assert_called_once_with(cx)

    @patch("pilo.normalize_system")
    @patch("pilo.restore_dataset")
    def test_execute_recovery_uses_normalize(self, mock_restore, mock_norm):
        cx = make_context()

        plan = pilo.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        pilo.execute_recovery_plan(plan, cx)

        mock_restore.assert_called_once()
        mock_norm.assert_called_once_with(cx)

    @patch("pilo.normalize_system")
    @patch("pilo.require_dataset")
    def test_init_uses_normalize(self, mock_require, mock_norm):
        cx = make_context()

        with patch("pilo.Context", return_value=cx):
            mod = import_command('init')
            mod.main()

        mock_norm.assert_called_once_with(cx)
