from pathlib import Path

from . import error
from . import paths


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
