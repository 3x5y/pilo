from pathlib import Path
import subprocess

from . import fs
from .util import as_user


def is_dirty(repo: Path):
    cmd = ["git", "-C", str(repo), "diff", "--quiet"]
    result = subprocess.run(cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode != 0


def ensure_repo(cx, path: Path):
    git_path = path / ".git"
    if not git_path.is_dir():
        fs.ensure_dir_owned(cx, path)
        cmd = "git -c init.defaultBranch=master init".split()
        args = [str(path)]
        as_user(cx.user, cmd + args, capture_output=True)


def commit_if_changed(cx, repo: Path, file: Path, message: str):

    cmd = ["git", "-C", str(repo), "add", str(file)]
    as_user(cx.user, cmd)
    cmd = ["git", "-C", str(repo), "diff", "--quiet", "--cached"]
    result = as_user(cx.user, cmd, check=False)

    if result.returncode != 0:
        cmd = ["git", "-C", str(repo), "commit", "-m", message]
        as_user(cx.user, cmd, capture_output=True)
