import filecmp
import os
import shutil
import subprocess
import sys

from contextlib import contextmanager
from pathlib import Path


def fatal(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def run(cmd, check=True):
    return subprocess.run(cmd, check=check)


def zfs_set_readonly(dataset, state):
    prop = 'on' if state else 'off'
    cmd = f'zfs set readonly={prop} {dataset}'
    subprocess.run(cmd.split(), check=True)


def zfs_get_readonly(dataset):
    cmd = 'zfs get -Ho value readonly ' + dataset
    result = subprocess.run(cmd.split(), capture_output=True,
                            text=True, check=True)
    return result.stdout.strip() == 'on'


def dataset_exists(dataset):
    result = subprocess.run(
        ["zfs", "list", dataset],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


@contextmanager
def dataset_writable(dataset):
    was = zfs_get_readonly(dataset)
    if was:
        zfs_set_readonly(dataset, False)
    try:
        yield
    finally:
        if was:
            zfs_set_readonly(dataset, True)


def require_dataset(dataset):
    if not dataset_exists(dataset):
        fatal(f"missing required dataset: {dataset}")


def list_files(root):
    return sorted(iter_files(root))


def iter_files(root):
    root = Path(root)
    for p in root.rglob("*"):
        if p.is_file():
            yield p


def files_equal(a, b):
    return filecmp.cmp(a, b, shallow=False)


def domain(rel: Path):
    parts = rel.parts
    if not parts:
        return "invalid"

    if parts[0] in ("in", "out", "sort"):
        return "pile"
    if parts[0] in ("collection", "filing"):
        return "static"
    return "invalid"


class Context:
    def __init__(self, environ=os.environ, args=None):
        self.intake_dataset = environ["PILO_INTAKE_DATASET"]
        self.pile_dataset = environ["PILO_PILE_DATASET"]
        self.static_dataset = environ["PILO_STATIC_DATASET"]
        self.admin_path = Path(environ["PILO_ADMIN_PATH"])
        self.intake_path = Path(environ["PILO_INTAKE_PATH"])
        self.pile_path = Path(environ["PILO_PILE_PATH"])
        self.static_path = Path(environ["PILO_STATIC_PATH"])
        self.user = environ["PILO_USER"]
        self.args = args and args[1:] or []

    def dataset_for(self, rel: Path):
        parts = rel.parts

        if parts[0] in ("in", "out", "sort"):
            return self.pile_dataset
        if parts[0] == "collection":
            return f"{self.static_dataset}/collection"
        if parts[0] == "filing":
            if len(parts) < 2:
                fatal("invalid filing path")
            return f"{self.static_dataset}/filing/{parts[1]}"

        fatal(f"no dataset for path: {rel}")

    def resolve_path(self, rel: Path):
        if rel.parts[0] in ("in", "out", "sort"):
            return self.pile_path / rel
        elif rel.parts[0] in ("collection", "filing"):
            return self.static_path / rel
        else:
            fatal(f"invalid path root: {rel}")

    def as_user(self, cmd):
        if os.geteuid() == 0:
            return subprocess.run(["sudo", "-u", self.user] + cmd, check=True)
        else:
            return subprocess.run(cmd, check=True)

    def ensure_owned(self, path):
        shutil.chown(path, self.user, self.user)

    def ensure_dir(self, path):
        self.as_user(["mkdir", "-p", path])

    def move(self, src, dst):
        self.ensure_dir(dst.parent)
        shutil.move(str(src), str(dst))
        self.ensure_owned(dst)

    def copy(self, src, dst):
        self.ensure_dir(dst.parent)
        shutil.copy2(str(src), str(dst))
        self.ensure_owned(dst)
