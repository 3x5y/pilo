from contextlib import contextmanager, ExitStack
from pathlib import Path
import filecmp
import hashlib
import shutil

from . import zfs


@contextmanager
def dataset_writable(dataset):
    was = zfs.get_readonly(dataset)
    if was:
        zfs.set_readonly(dataset, False)
    try:
        yield
    finally:
        if was:
            zfs.set_readonly(dataset, True)


@contextmanager
def writable_datasets(datasets):
    seen = []
    for ds in datasets:
        if ds not in seen:
            seen.append(ds)

    with ExitStack() as stack:
        for ds in seen:
            stack.enter_context(dataset_writable(ds))
        yield


def list_files(root):
    return sorted(iter_files(root))


def iter_files(root):
    root = Path(root)
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def ensure_parent_dir(cx, path: Path):
    ensure_dir_owned(cx, path.parent)


def ensure_dir_owned(cx, path: Path):
    path = Path(path)

    missing = []

    cur = path

    while not cur.exists():
        missing.append(cur)
        cur = cur.parent

    path.mkdir(parents=True, exist_ok=True)

    for d in reversed(missing):
        cx.ensure_owned(d)


def safe_copy(cx, src: Path, dst: Path):
    ensure_parent_dir(cx, dst)
    cx.ensure_owned(dst.parent)
    shutil.copy2(src, dst)
    cx.ensure_owned(dst)


def safe_move(cx, src: Path, dst: Path):
    ensure_parent_dir(cx, dst)
    cx.ensure_owned(dst.parent)
    shutil.move(src, dst)
    cx.ensure_owned(dst)


def safe_unlink(path: Path):
    path.unlink()


def safe_rmdir(path: Path):
    path.rmdir()


def files_equal(a, b):
    return filecmp.cmp(a, b, shallow=False)


def sha256_file(path: Path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()