from . import error
from . import fs
from . import zfs


def require_dataset(dataset):
    if not zfs.dataset_exists(dataset):
        error.fatal(f"missing required dataset: {dataset}")


def require_new_dataset(dataset):
    if zfs.dataset_exists(dataset):
        error.fatal(f"dataset exists: {dataset}")


def require_snapshot(snapshot):
    if not zfs.snapshot_exists(snapshot):
        error.fatal(f"missing snapshot: {snapshot}")


def require_snapshot_of_dataset(snap, dataset):
    require_snapshot(snap)
    if not snap.startswith(dataset + "@"):
        error.fatal(f"snapshot {snap} does not belong to {dataset}")


def require_latest_snapshot(dataset, role):
    snapshot = zfs.latest_snapshot(dataset)
    if not snapshot:
        error.fatal(f"no {role} snapshot")
    return snapshot


def require_within_dataset(target, root):
    if not target == root and not target.startswith(root + "/"):
        error.fatal(f"{target} outside {root}")


def require_file(path):
    if not path.is_file():
        error.fatal(f"file does not exist: {path}")


def require_no_conflict(src, dst):
    if dst.is_file() and not fs.files_equal(src, dst):
        error.fatal(f"destination conflict: {dst}")


def require_verified(checksum):
    from pilo.manifest_model import ChecksumProvenance
    if checksum.provenance != ChecksumProvenance.VERIFIED:
        error.fatal("checksum continuity not verified")
    return checksum
