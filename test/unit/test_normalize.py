import unittest
from unittest.mock import call
from unittest.mock import patch

from pilo import normalize
from pilo.back import recover
import pilotest


class TestNormalize(pilotest.TestCase):

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contracts")
    def test_normalize_applies_contract(self, mock_contract, mock_run,
                                        mock_dirs, mock_owner):

        cx = pilotest.make_context()
        normalize.normalize_system(cx)
        mock_contract.assert_called_once_with(cx)

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("pilo.zfs.run")
    @patch("pilo.normalize.apply_dataset_contracts")
    def test_normalize_mounts(self, mock_contract, mock_run, mock_dirs,
                              mock_owner):

        cx = pilotest.make_context()
        normalize.normalize_system(cx)
        mock_run.assert_called_once_with(["zfs", "mount", "-a"])

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contracts")
    def test_normalize_ensures_runtime_dirs(
        self, mock_contract, mock_run, mock_dirs, mock_owner
    ):

        cx = pilotest.make_context()
        normalize.normalize_system(cx)
        mock_dirs.assert_called_once_with(cx)

    @patch("pilo.normalize.apply_ownership")
    @patch("pilo.normalize.ensure_runtime_dirs")
    @patch("subprocess.run")
    @patch("pilo.normalize.apply_dataset_contracts")
    def test_normalize_applies_ownership(
        self, mock_contract, mock_run, mock_dirs, mock_owner
    ):
        cx = pilotest.make_context()

        normalize.normalize_system(cx)

        mock_owner.assert_called_once_with(cx)

    @patch("pilo.normalize.normalize_system")
    @patch("pilo.back.restore.restore_dataset")
    def test_execute_recovery_uses_normalize(self, mock_restore, mock_norm):
        cx = pilotest.make_context()

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
        cx = pilotest.make_context()

        with patch("pilo.context.Context", return_value=cx):
            mod = pilotest.import_command('init')
            mod.main()

        mock_norm.assert_called_once_with(cx)



class TestDatasetContracts(pilotest.TestCase):

    def test_contract_registry_order(self):
        names = [
            c.name
            for c in normalize.dataset_contracts.ALL
        ]

        self.assertEqual(
            names,
            [
                "active",
                "admin",
                "pile-intake",
                "pile-readonly",
                "static",
                "collection",
                "filing",
            ],
        )

    def test_lookup_contract(self):
        c = normalize.dataset_contracts.lookup(
            "collection"
        )

        self.assertEqual(c.name, "collection")
        self.assertTrue(c.readonly)
        self.assertTrue(c.filesystem)

    @patch("pilo.normalize.apply_namespace")
    @patch("pilo.normalize.apply_filesystem")
    def test_apply_dataset_contract_uses_registry(
        self,
        apply_fs,
        apply_ns,
    ):
        cx = pilotest.make_context()

        normalize.apply_dataset_contracts(cx)

        apply_ns.assert_has_calls([
            call("tank/a/active", mountpoint=None),
            call("tank/a/static", mountpoint=None),
        ])

        apply_fs.assert_has_calls([
            call(
                "tank/a/active/admin",
                readonly=False,
                mountpoint=cx.admin_path,
            ),
            call(
                "tank/a/active/pile-intake",
                readonly=False,
                mountpoint=cx.intake_path,
            ),
            call(
                "tank/a/active/pile-readonly",
                readonly=True,
                mountpoint=cx.pile_path,
            ),
            call(
                "tank/a/static/collection",
                readonly=True,
                mountpoint=cx.collection_path,
            ),
        ])


    @patch("pilo.zfs.dataset_exists")
    def test_missing_dataset(self, exists):

        exists.return_value = False

        cx = pilotest.make_context()

        issues = normalize.validate_dataset_contracts(cx)

        self.assertTrue(issues)

        self.assertEqual(
            issues[0].code,
            "missing.required.dataset",
        )

    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.get_readonly")
    def test_invalid_readonly(
        self,
        get_readonly,
        exists,
    ):

        exists.return_value = True
        get_readonly.return_value = False

        cx = pilotest.make_context()

        contract = normalize.dataset_contracts.lookup(
            "pile-readonly"
        )

        issues = normalize.validate_dataset_contract(
            cx,
            contract,
        )

        self.assertEqual(
            issues[0].code,
            "invalid.readonly",
        )

    @patch("pilo.zfs.dataset_exists")
    @patch("pilo.zfs.get_readonly")
    def test_contract_ok(
        self,
        get_readonly,
        exists,
    ):

        exists.return_value = True
        get_readonly.return_value = True

        cx = pilotest.make_context()

        contract = normalize.dataset_contracts.lookup(
            "pile-readonly"
        )

        issues = normalize.validate_dataset_contract(
            cx,
            contract,
        )

        self.assertEqual(issues, [])
