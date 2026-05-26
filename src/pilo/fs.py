from pathlib import Path
import filecmp
import hashlib
import os
import shutil


def list_files(root):
    return sorted(iter_files(root))


def iter_files(root):
    root = Path(root)
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def ensure_owned(cx, path):
    stat = os.stat(path)
    if not stat.st_uid == stat.st_gid == cx.user_id:
        shutil.chown(path, cx.user, cx.user)


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
        ensure_owned(cx, d)


def safe_copy(cx, src: Path, dst: Path):
    ensure_parent_dir(cx, dst)
    ensure_owned(cx, dst.parent)
    shutil.copy2(src, dst)
    ensure_owned(cx, dst)


def safe_move(cx, src: Path, dst: Path):
    ensure_parent_dir(cx, dst)
    ensure_owned(cx, dst.parent)
    shutil.move(src, dst)
    ensure_owned(cx, dst)


def safe_unlink(path: Path):
    path.unlink()


def safe_rmdir(path: Path):
    path.rmdir()


def files_equal(a, b):
    return filecmp.cmp(a, b, shallow=False)


CHUNK_SIZE = 1024 * 1024


def hash_file(h, path: Path, chunk_size):
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def sha256_file(path: Path, chunk_size=CHUNK_SIZE):
    h = hashlib.sha256()
    return hash_file(h, path, chunk_size=chunk_size)


def sha512_file(path: Path, chunk_size=CHUNK_SIZE):
    h = hashlib.sha512()
    return hash_file(h, path, chunk_size=chunk_size)


def b2_file(path: Path, chunk_size=CHUNK_SIZE):
    h = hashlib.blake2b()
    return hash_file(h, path, chunk_size=chunk_size)


hash_file1 = sha256_file
hash_file2 = b2_file
