from . import checks
from . import normalize
from . import zfs


def create_namespace(dataset):
    zfs.create_dataset(dataset)


def create_filesystem(dataset):
    zfs.create_dataset(dataset)


def provision_primary(cx):

    checks.require_new_dataset(cx.root_dataset)

    create_namespace(cx.root_dataset)
    create_namespace(cx.active_dataset)
    create_namespace(cx.static_dataset)
    create_namespace(cx.filing_dataset)

    create_filesystem(cx.admin_dataset)
    create_filesystem(cx.intake_dataset)
    create_filesystem(cx.pile_dataset)
    create_filesystem(cx.collection_dataset)

    normalize.normalize_system(cx)


def provision_secondary(root):
    checks.require_new_dataset(root)
    create_namespace(root)
