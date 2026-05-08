from dataclasses import dataclass
from pathlib import Path
import os
import pwd
import shutil
import subprocess
import sys

import pilo
from .paths import parse_logical_path, ResolvedPath, StorageDomain
from .validation import require_child_dataset


@dataclass(frozen=True)
class DatasetMapping:
    src_root: str
    dst_root: str

    def _suffix(self, dataset: str, root: str) -> str:
        require_child_dataset(dataset, root)
        return dataset[len(root):].lstrip("/")

    def map(self, dataset: str) -> str:
        suffix = self._suffix(dataset, self.src_root)
        return f"{self.dst_root}/{suffix}" if suffix else self.dst_root

    def inverse(self, dataset: str) -> str:
        suffix = self._suffix(dataset, self.dst_root)
        return f"{self.src_root}/{suffix}" if suffix else self.src_root

    def validate_within_src(self, dataset: str):
        require_child_dataset(dataset, self.src_root)

    def validate_within_dst(self, dataset: str):
        require_child_dataset(dataset, self.dst_root)


class Context:
    def __init__(self, environ=os.environ, args=sys.argv):
        self.root_dataset = environ["PILO_ROOT"]
        self.replica_dataset = environ["PILO_REPLICA_ROOT"]
        self.admin_dataset = environ["PILO_ADMIN_DATASET"]
        self.intake_dataset = environ["PILO_INTAKE_DATASET"]
        self.pile_dataset = environ["PILO_PILE_DATASET"]
        self.static_dataset = environ["PILO_STATIC_DATASET"]
        self.collection_dataset = f"{self.static_dataset}/collection"
        self.filing_dataset = f"{self.static_dataset}/filing"

        self.path = Path(environ["PILO_PATH"])
        self.admin_path = Path(environ["PILO_ADMIN_PATH"])
        self.intake_path = Path(environ["PILO_INTAKE_PATH"])
        self.pile_path = Path(environ["PILO_PILE_PATH"])
        self.static_path = Path(environ["PILO_STATIC_PATH"])
        #self.collection_path = Path(environ["PILO_COLLECTION_PATH"])
        #self.filing_path = Path(environ["PILO_FILING_PATH"])
        self.collection_path = self.static_path / 'collection'
        self.filing_path = self.static_path / 'filing'

        self.user = environ["PILO_USER"]
        self.user_id = pwd.getpwnam(self.user).pw_uid
        self.args = args and args[1:] or []

    def resolve(self, rel: Path) -> ResolvedPath:
        logical = parse_logical_path(rel)

        if logical.domain == StorageDomain.PILE:
            return ResolvedPath(
                logical=logical,
                physical=self.pile_path / logical.relpath,
                dataset=self.pile_dataset,
            )

        if logical.domain == StorageDomain.COLLECTION:
            return ResolvedPath(
                logical=logical,
                physical=self.collection_path / logical.relpath,
                dataset=self.collection_dataset,
            )

        if logical.domain == StorageDomain.FILING:
            subset = logical.relpath.parts[0]

            return ResolvedPath(
                logical=logical,
                physical=self.filing_path / logical.relpath,
                dataset=f"{self.filing_dataset}/{subset}",
            )

        raise AssertionError("unreachable")

    def as_user(self, cmd, check=True, **kw):
        if os.geteuid() == 0:
            return subprocess.run(["sudo", "-u", self.user] + cmd,
                                  check=check,
                                  **kw)
        else:
            return subprocess.run(cmd, check=check, **kw)

    def ensure_owned(self, path):
        stat = os.stat(path)
        if not stat.st_uid == stat.st_gid == self.user_id:
            shutil.chown(path, self.user, self.user)

    def ensure_dir(self, path):
        pilo.ensure_dir_owned(self, path)

    def move(self, src, dst):
        pilo.safe_move(self, src, dst)

    def copy(self, src, dst):
        pilo.safe_copy(self, src, dst)

    def copy_static(self, src, resolved):
        with pilo.dataset_writable(resolved.dataset):
            self.copy(src, resolved.path)

    def remove_piled(self, path):
        with pilo.dataset_writable(self.pile_dataset):
            pilo.safe_unlink(path)

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


