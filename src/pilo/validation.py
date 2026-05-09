from pathlib import Path

from . import checks
from . import error
from . import fs
from . import paths
from . import zfs


require_dataset = checks.require_dataset
require_new_dataset = checks.require_new_dataset
require_snapshot = checks.require_snapshot
require_snapshot_of_dataset =  checks.require_snapshot_of_dataset
require_within_dataset = checks.require_within_dataset
require_file = checks.require_file
require_no_conflict = checks.require_no_conflict


def require_child_dataset(dataset, root):
    if not dataset.startswith(root):
        error.fatal(f"dataset outside root: {dataset}")


def require_relative_path(path: Path):
    if path.is_absolute():
        error.fatal("absolute paths not allowed")
    if ".." in path.parts:
        error.fatal("parent traversal not allowed")


def require_same_domain(src, dst):
    try:
        lsrc = paths.try_parse_logical_path(src)
        ldst = paths.try_parse_logical_path(dst)
    except paths.PathParseError as e:
        error.fatal(str(e))
    if lsrc.domain != ldst.domain:
        error.fatal("cross-domain move not allowed")


class validate:
    @staticmethod
    def dataset_exists(ds):
        checks.require_dataset(ds)

    @staticmethod
    def snapshot_exists(snap):
        checks.require_snapshot(snap)

    @staticmethod
    def new_dataset(ds):
        checks.require_new_dataset(ds)


