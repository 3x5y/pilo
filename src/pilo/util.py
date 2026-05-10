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
