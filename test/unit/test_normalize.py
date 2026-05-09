import unittest
from unittest.mock import patch

from pilo import normalize
from pilo.back import recover
from pilotest import make_context, import_command


class TestNormalize(unittest.TestCase):

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contract")
    def test_normalize_applies_contract(self, mock_contract, mock_run,
                                        mock_dirs, mock_owner):

        cx = make_context()
        normalize.normalize_system(cx)
        mock_contract.assert_called_once_with(cx)

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contract")
    def test_normalize_mounts(self, mock_contract, mock_run, mock_dirs,
                              mock_owner):

        cx = make_context()
        normalize.normalize_system(cx)
        mock_run.assert_called_once_with(["zfs", "mount", "-a"], check=True)

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contract")
    def test_normalize_ensures_runtime_dirs(
        self, mock_contract, mock_run, mock_dirs, mock_owner
    ):

        cx = make_context()
        normalize.normalize_system(cx)
        mock_dirs.assert_called_once_with(cx)

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contract")
    def test_normalize_applies_ownership(
        self, mock_contract, mock_run, mock_dirs, mock_owner
    ):
        cx = make_context()

        normalize.normalize_system(cx)

        mock_owner.assert_called_once_with(cx)

    @patch("pilo.normalize.normalize_system")
    @patch("pilo.back.restore.restore_dataset")
    def test_execute_recovery_uses_normalize(self, mock_restore, mock_norm):
        cx = make_context()

        plan = recover.RecoveryPlan(
            target="tank/a",
            replica="backup/a",
            snapshot="backup/a@r-1",
            recursive=True,
        )

        recover.execute_recovery_plan(plan, cx)

        mock_restore.assert_called_once()
        mock_norm.assert_called_once_with(cx)

    @patch("pilo.normalize.normalize_system")
    @patch("pilo.checks.require_dataset")
    def test_init_uses_normalize(self, mock_require, mock_norm):
        cx = make_context()

        with patch("pilo.context.Context", return_value=cx):
            mod = import_command('init')
            mod.main()

        mock_norm.assert_called_once_with(cx)
