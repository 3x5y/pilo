import unittest
from unittest.mock import patch

from pilo import provision
import pilotest

class TestProvision(pilotest.TestCase):
    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_provision_primary_rejects_existing_root(self, *_):

        cx = pilotest.make_context()

        with self.assert_fatal():
            provision.provision_primary(cx)

    @patch("pilo.normalize.normalize_system")
    @patch("pilo.zfs.dataset_exists", return_value=False)
    @patch("pilo.zfs.create_dataset")
    def test_provision_primary_creates_contract_tree(self, create, *_):
        cx = pilotest.make_context()

        provision.provision_primary(cx)

        create.assert_any_call(cx.root_dataset)
        create.assert_any_call(cx.active_dataset)
        create.assert_any_call(cx.admin_dataset)
        create.assert_any_call(cx.pile_dataset)
        create.assert_any_call(cx.intake_dataset)
        create.assert_any_call(cx.static_dataset)
        create.assert_any_call(cx.collection_dataset)
        create.assert_any_call(cx.filing_dataset)

    @patch("pilo.zfs.dataset_exists", return_value=True)
    def test_provision_secondary_rejects_existing_root(self, *_):

        cx = pilotest.make_context()

        with self.assert_fatal():
            provision.provision_secondary(cx)

    @patch("pilo.normalize.normalize_system")
    @patch("pilo.zfs.dataset_exists", return_value=False)
    @patch("pilo.zfs.create_dataset")
    def test_provision_secondary_creates_contract_tree(self, create, *_):

        provision.provision_secondary('backup/z')

        create.assert_any_call('backup/z')
