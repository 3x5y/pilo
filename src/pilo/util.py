from datetime import datetime
from pathlib import Path
import subprocess

from . import zfs


def run(cmd, check=True):
    return subprocess.run(cmd, check=check)


def now_epoch():
    return int(datetime.now().timestamp())


def git_dirty(repo: Path):
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--quiet"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode != 0


def snapshot_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def find_incremental_base(src, dst):
    guid = zfs.get_latest_guid(dst)
    if not guid:
        return None
    for name, g in zfs.snapshot_guids(src):
        if g == guid:
            return name
    return None