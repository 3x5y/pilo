from . import checks
from . import fs
from . import zfs


def apply_dataset_contract(cx):

    apply_namespace(cx.root_dataset + '/active')
    apply_filesystem(cx.root_dataset + '/active/admin',
                     readonly=False,
                     mountpoint=cx.admin_path)
    apply_filesystem(cx.root_dataset + '/active/pile-intake',
                     readonly=False,
                     mountpoint=cx.intake_path)
    apply_filesystem(cx.root_dataset + '/active/pile-readonly',
                     readonly=True,
                     mountpoint=cx.pile_path)

    apply_namespace(cx.root_dataset + '/static')
    apply_filesystem(cx.root_dataset + '/static/collection',
                     readonly=True,
                     mountpoint=cx.collection_path)

    apply_namespace(cx.root_dataset + '/static/filing',
                    mountpoint=cx.filing_path)


def apply_namespace(dataset, mountpoint=None):
    checks.require_dataset(dataset)
    if mountpoint:
        zfs.set_mountpoint(dataset, mountpoint)
    zfs.set_canmount(dataset, False)


def apply_filesystem(dataset, mountpoint, readonly):
    checks.require_dataset(dataset)
    zfs.set_readonly(dataset, readonly)
    zfs.set_mountpoint(dataset, mountpoint)
    zfs.set_canmount(dataset, True)


def apply_ownership(cx):
    fs.ensure_owned(cx, cx.admin_path)
    fs.ensure_owned(cx, cx.intake_path)
    with fs.dataset_writable(cx.pile_dataset):
        fs.ensure_owned(cx, cx.pile_path)
    with fs.dataset_writable(cx.collection_dataset):
        fs.ensure_owned(cx, cx.collection_path)


def ensure_runtime_dirs(cx):
    pile = cx.pile_path
    with fs.dataset_writable(cx.pile_dataset):
        fs.ensure_dir_owned(cx, pile / "in")
        fs.ensure_dir_owned(cx, pile / "sort")
        fs.ensure_dir_owned(cx, pile / "out")
        fs.ensure_dir_owned(cx, pile / "out" / "collection")
        fs.ensure_dir_owned(cx, pile / "out" / "filing")


def normalize_system(cx):
    apply_dataset_contract(cx)
    zfs.mount()
    ensure_runtime_dirs(cx)
    apply_ownership(cx)
