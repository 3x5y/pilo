import unittest
from unittest.mock import patch

import pilo
import helpers


make_context = helpers.make_context


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
            mod = helpers.import_command('init')
            mod.main()

        mock_norm.assert_called_once_with(cx)
