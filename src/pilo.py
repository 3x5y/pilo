import filecmp
import os
import subprocess
import sys

from contextlib import contextmanager


def fatal(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def require_env(name):
    val = os.environ.get(name)
    if not val:
        fatal(f"{name} not set in environment")
    return val


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
    files = []
    for base, _, filenames in os.walk(root):
        for f in filenames:
            files.append(os.path.join(base, f))
    return sorted(files)


def ensure_dir(path, user):
    if not os.path.isdir(path):
        run(["sudo", "-u", user, "mkdir", "-p", path])


def files_equal(a, b):
    return filecmp.cmp(a, b, shallow=False)


def as_user(cmd):
    user = os.environ.get("PILO_USER")
    if not user:
        fatal("PILO_USER not set")

    if os.geteuid() == 0:
        return subprocess.run(["sudo", "-u", user] + cmd, check=True)
    else:
        return subprocess.run(cmd, check=True)


def files_under(path):
    result = []
    for root, _, files in os.walk(path):
        for f in files:
            result.append(os.path.join(root, f))
    return result
