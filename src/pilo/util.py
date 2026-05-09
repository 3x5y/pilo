from datetime import datetime
from pathlib import Path
import os
import subprocess

from . import fs


def run(cmd, check=True):
    return subprocess.run(cmd, check=check)


def now_epoch():
    return int(datetime.now().timestamp())


def snapshot_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def as_user(user, cmd, check=True, **kw):
    if os.geteuid() == 0:
        return subprocess.run(["sudo", "-u", user] + cmd,
                              check=check,
                              **kw)
    else:
        return subprocess.run(cmd, check=check, **kw)


def git_dirty(repo: Path):
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--quiet"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode != 0


def ensure_git_repo(cx, path: Path):
    git_path = path / ".git"
    if not git_path.is_dir():
        fs.ensure_dir_owned(cx, path)
        cmd = ["git", "-c", "init.defaultBranch=master", "init", str(path)]
        as_user(cx.user, cmd, capture_output=True)


def git_commit_if_changed(cx, repo: Path, file: Path, message: str):
    cmd = ["git", "-C", str(repo), "add", str(file)]
    as_user(cx.user, cmd)

    cmd = ["git", "-C", str(repo), "diff", "--quiet", "--cached"]
    result = as_user(cx.user, cmd, check=False)

    if result.returncode != 0:
        cmd = [ "git", "-C", str(repo), "commit", "-m", message]
        as_user(cx.user, cmd, capture_output=True)
