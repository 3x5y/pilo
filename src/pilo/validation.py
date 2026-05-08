from pathlib import Path

import pilo

from . import zfs


def require_dataset(dataset):
    if not zfs.dataset_exists(dataset):
        pilo.fatal(f"missing required dataset: {dataset}")


def require_new_dataset(dataset):
    if zfs.dataset_exists(dataset):
        pilo.fatal(f"destination exists: {dataset}")


def require_child_dataset(dataset, root):
    if not dataset.startswith(root):
        pilo.fatal(f"dataset outside root: {dataset}")


def require_snapshot(snapshot):
    if not zfs.snapshot_exists(snapshot):
        pilo.fatal(f"missing snapshot: {snapshot}")


def require_snapshot_of_dataset(snap, dataset):
    require_snapshot(snap)
    if not snap.startswith(dataset + "@"):
        pilo.fatal(f"snapshot {snap} does not belong to {dataset}")


def require_within_dataset(target, root):
    if not target == root and not target.startswith(root + "/"):
        pilo.fatal(f"{target} outside {root}")


def require_file(path):
    if not path.is_file():
        pilo.fatal(f"file does not exist: {path}")


def require_no_conflict(src, dst):
    if dst.is_file() and not pilo.files_equal(src, dst):
        pilo.fatal(f"destination conflict: {dst}")


def require_relative_path(path: Path):
    if path.is_absolute():
        pilo.fatal("absolute paths not allowed")
    if ".." in path.parts:
        pilo.fatal("parent traversal not allowed")


def require_same_domain(src, dst):
    src_domain = pilo.domain(src)
    dst_domain = pilo.domain(dst)

    if src_domain != dst_domain:
        pilo.fatal("cross-domain move not allowed")


class validate:
    @staticmethod
    def dataset_exists(ds):
        require_dataset(ds)

    @staticmethod
    def snapshot_exists(snap):
        require_snapshot(snap)

    @staticmethod
    def new_dataset(ds):
        require_new_dataset(ds)


