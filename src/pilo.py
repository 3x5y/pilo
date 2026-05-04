import filecmp
import hashlib
import os
import shutil
import subprocess
import sys

from contextlib import contextmanager
from dataclasses import dataclass
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
    result = subprocess.run(cmd.split(),
                            capture_output=True,
                            text=True,
                            check=True)
    return result.stdout.strip() == 'on'


def dataset_exists(dataset):
    result = subprocess.run(
        ["zfs", "list", dataset],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def generate_manifest_lines(root: Path):
    for path in sorted(iter_files(root)):
        rel = path.relative_to(root)
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        yield f"{h}  ./{rel}"


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


@dataclass
class Resolved:
    path: Path
    dataset: str


class Context:
    def __init__(self, environ=os.environ, args=sys.argv):
        self.intake_dataset = environ["PILO_INTAKE_DATASET"]
        self.pile_dataset = environ["PILO_PILE_DATASET"]
        self.static_dataset = environ["PILO_STATIC_DATASET"]
        self.admin_path = Path(environ["PILO_ADMIN_PATH"])
        self.intake_path = Path(environ["PILO_INTAKE_PATH"])
        self.pile_path = Path(environ["PILO_PILE_PATH"])
        self.static_path = Path(environ["PILO_STATIC_PATH"])
        self.user = environ["PILO_USER"]
        self.args = args and args[1:] or []

    def _resolve(self, rel: Path) -> Resolved:
        if not rel.parts:
            fatal("empty path")

        top = rel.parts[0]
        if top in ("in", "out", "sort"):
            return Resolved(
                path=self.pile_path / rel,
                dataset=self.pile_dataset,
            )
        if top == "collection":
            return Resolved(
                path=self.static_path / rel,
                dataset=f"{self.static_dataset}/collection",
            )
        if top == "filing":
            if len(rel.parts) < 2:
                fatal("invalid filing path")
            subset = rel.parts[1]
            return Resolved(
                path=self.static_path / rel,
                dataset=f"{self.static_dataset}/filing/{subset}",
            )
        fatal(f"invalid path: {rel}")

    def resolve_path_dataset(self, rel: Path):
        r = self._resolve(rel)
        return r.path, r.dataset

    def resolve_path(self, rel: Path):
        return self._resolve(rel).path

    def resolve_dataset(self, rel: Path):
        return self._resolve(rel).dataset

    def as_user(self, cmd, check=True, **kw):
        if os.geteuid() == 0:
            return subprocess.run(["sudo", "-u", self.user] + cmd,
                                  check=check,
                                  **kw)
        else:
            return subprocess.run(cmd, check=check, **kw)

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

    def ensure_git_repo(self, path: Path):
        git_path = path / ".git"
        if not git_path.is_dir():
            self.ensure_dir(path)
            cmd = ["git", "-c", "init.defaultBranch=master", "init", str(path)]
            self.as_user(cmd, capture_output=True)

    def git_commit_if_changed(self, repo: Path, file: Path, message: str):
        cmd = ["git", "-C", str(repo), "add", str(file)]
        self.as_user(cmd)

        cmd = ["git", "-C", str(repo), "diff", "--quiet", "--cached"]
        result = self.as_user(cmd, check=False)

        if result.returncode != 0:
            cmd = [ "git", "-C", str(repo), "commit", "-m", message]
            self.as_user(cmd, capture_output=True)
