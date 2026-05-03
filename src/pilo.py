import filecmp
import os
import subprocess
import sys


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


def dataset_exists(dataset):
    result = subprocess.run(
        ["zfs", "list", dataset],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


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


def file_equal(a, b):
    return subprocess.run(["cmp", "-s", a, b]).returncode == 0


def with_writable(dataset, fn):
    try:
        subprocess.run(["zfs", "set", "readonly=off", dataset], check=True)
        return fn()
    finally:
        subprocess.run(["zfs", "set", "readonly=on", dataset], check=True)


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
