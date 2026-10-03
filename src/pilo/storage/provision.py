from .. import checks
from . import normalize
from .. import zfs


def create_namespace(dataset):
    zfs.create_dataset(dataset)


def create_filesystem(dataset):
    zfs.create_dataset(dataset)


def provision_primary(cx):

    checks.require_new_dataset(cx.root_dataset)
    create_namespace(cx.root_dataset)

    for contract in normalize.dataset_contracts.ALL:
        if not contract.filesystem:
            dataset = normalize.contract_dataset(cx, contract)
            create_namespace(dataset)

    for contract in normalize.dataset_contracts.ALL:
        if contract.filesystem:
            dataset = normalize.contract_dataset(cx, contract)
            create_filesystem(dataset)

    normalize.normalize_system(cx)


def provision_secondary(root):
    checks.require_new_dataset(root)
    create_namespace(root)
