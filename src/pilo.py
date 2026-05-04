import filecmp
import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime
from enum import Enum

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


def fatal(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


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


#####################
# static file stuff #
#####################


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
        self.admin_dataset = environ["PILO_ADMIN_DATASET"]
        self.intake_dataset = environ["PILO_INTAKE_DATASET"]
        self.pile_dataset = environ["PILO_PILE_DATASET"]
        self.static_dataset = environ["PILO_STATIC_DATASET"]

        self.collection_dataset = f"{self.static_dataset}/collection"
        self.filing_dataset = f"{self.static_dataset}/filing"

        self.admin_path = Path(environ["PILO_ADMIN_PATH"])
        self.intake_path = Path(environ["PILO_INTAKE_PATH"])
        self.pile_path = Path(environ["PILO_PILE_PATH"])
        self.static_path = Path(environ["PILO_STATIC_PATH"])
        self.user = environ["PILO_USER"]
        self.args = args and args[1:] or []

    def resolve(self, rel: Path) -> Resolved:
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

    def copy_static(self, src, resolved):
        with dataset_writable(resolved.dataset):
            self.copy(src, resolved.path)

    def remove_piled(self, path):
        with dataset_writable(self.pile_dataset):
            path.unlink()

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


#####################
# replication stuff #
#####################


class ReplicationStatus(Enum):
    OK = "OK"
    EMPTY = "EMPTY"
    BEHIND = "BEHIND"
    DIVERGED = "DIVERGED"
    UNKNOWN = "UNKNOWN"


def _find_incremental_base(src, dst):
    guid = get_latest_guid(dst)
    if not guid:
        return None
    for name, g in zfs_snapshot_guids(src):
        if g == guid:
            return name
    return None


def _replicate_full(snapshot, dst):
    send = ["zfs", "send", "-R", snapshot]
    recv = ["zfs", "receive", "-h", "-u", "-o", "readonly=on", dst]
    simple_pipe(send, recv)


def _replicate_incremental(base, snapshot, dst):
    send = ["zfs", "send", "-h", "-R", "-I", base, snapshot]
    recv = ["zfs", "receive", "-u", "-o", "readonly=on", dst]
    simple_pipe(send, recv)


def _map_dataset(name, src_root, dst_root):
    suffix = name[len(src_root):].lstrip("/")
    return f"{dst_root}/{suffix}" if suffix else dst_root


def simple_pipe(src_cmd, sink_cmd):
    source = subprocess.Popen(src_cmd, stdout=subprocess.PIPE)
    sink = subprocess.Popen(sink_cmd, stdin=source.stdout)
    source.stdout.close()
    sink.communicate()
    if source.wait() != 0 or sink.returncode != 0:
        fatal("replication failed")


def zfs_list_filesystems(root):
    result = subprocess.run(
        ["zfs", "list", "-r", "-t", "filesystem", "-Ho", "name", root],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def zfs_list_guids(dataset):
    result = subprocess.run(
        ["zfs", "list", "-t", "snapshot", "-Ho", "guid", dataset],
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(result.stdout.splitlines())


def zfs_list_snapshots(dataset):
    cmd = 'zfs list -t snapshot -Ho name -s creation ' + dataset
    result = subprocess.run(
        cmd.split(),
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.strip().splitlines() if line]


def zfs_latest_snapshot(dataset):
    try:
        snaps = zfs_list_snapshots(dataset)
    except subprocess.CalledProcessError:
        return None
    else:
        return snaps and snaps[-1] or None


def zfs_snapshot_guids(dataset):
    result = subprocess.run(
        ["zfs", "list", "-t", "snapshot", "-o", "name,guid", dataset],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().splitlines()
    return [line.split() for line in lines if line]


def get_latest_guid(dataset):
    result = subprocess.run(
        ["zfs", "list", "-t", "snapshot", "-Ho", "guid", "-s", "creation", dataset],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = result.stdout.strip().splitlines()
    return lines[-1] if lines else None


def snapshot_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def zfs_snapshot(name: str, dataset: str):
    if not dataset:
        fatal("dataset required for snapshot")
    cmd = ["zfs", "snapshot", "-r", f"{dataset}@{name}"]
    subprocess.run(cmd, check=True)


def create_snapshot(name, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]
    zfs_snapshot(name, dataset)
    return f"{dataset}@{name}"


def create_anchor(anchor_type, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]

    ts = snapshot_timestamp()

    if anchor_type == "daily":
        name = f"daily-{ts}"
        hold = False
    elif anchor_type == "rotation":
        name = f"rotation-{ts}"
        hold = True
    else:
        fatal("invalid anchor type")

    snap = create_snapshot(name, dataset)

    if hold:
        zfs_hold("repl-anchor", snap)

    return snap


def create_prefixed_snapshot(prefix, dataset=None):
    ts = snapshot_timestamp()
    name = f"{prefix}-{ts}"
    return create_snapshot(name, dataset)


def zfs_hold(tag, snapshot):
    cmd = ["zfs", "hold", "-r", "repl-anchor", snapshot]
    subprocess.run(cmd, check=True)


def replicate(src, dst):
    last_src = zfs_latest_snapshot(src)
    last_dst = zfs_latest_snapshot(dst)

    if not last_src:
        fatal("no source snapshot")

    if not last_dst:
        return _replicate_full(last_src, dst)

    base = _find_incremental_base(src, dst)

    if not base:
        fatal(f"base snapshot missing on source: {base}")

    if base == last_src:
        return  # idempotent

    return _replicate_incremental(base, last_src, dst)


def replication_status(src, dst):
    src_guid = get_latest_guid(src)
    dst_guid = get_latest_guid(dst)

    if not dst_guid:
        return ReplicationStatus.EMPTY, "no snapshots on target"

    for dst_ds in zfs_list_filesystems(dst):
        src_ds = _map_dataset(dst_ds, dst, src)

        src_guids = set(zfs_list_guids(src_ds))
        dst_guids = set(zfs_list_guids(dst_ds))

        if dst_guids - src_guids:
            return ReplicationStatus.DIVERGED, f"divergence in {dst_ds}"

        if get_latest_guid(src_ds) != get_latest_guid(dst_ds):
            return ReplicationStatus.BEHIND, f"behind in {dst_ds}"

    for src_ds in zfs_list_filesystems(src):
        dst_ds = _map_dataset(src_ds, src, dst)
        if not dataset_exists(dst_ds):
            return ReplicationStatus.BEHIND, f"missing {dst_ds}"

    if src_guid != dst_guid:
        return ReplicationStatus.UNKNOWN, "root GUID mismatch"

    return ReplicationStatus.OK, None


################
# status stuff #
################


class Status:
    def __init__(self):
        self.code = 0

    def warn(self, msg):
        print(f"[WARN] {msg}")
        self.code = 1

    def ok(self, msg):
        print(f"[OK] {msg}")


def now_epoch():
    return int(datetime.now().timestamp())


def git_dirty(repo: Path):
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--quiet"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode != 0


def zfs_latest_snapshot_with_time(dataset):
    cmd = ["zfs", "list", "-p", "-t", "snapshot", "-o", "name,creation", "-s", "creation", dataset]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    lines = [l for l in result.stdout.splitlines() if l.startswith(dataset + "@")]

    if not lines:
        return None, None

    name, ts = lines[-1].split()

    try:
        return name, int(ts)
    except Exception:
        return name, None


#####################
#  recovery stuff   #
#####################


def zfs_destroy(dataset, recursive=True):
    cmd = ["zfs", "destroy"]
    if recursive:
        cmd.append("-r")
    cmd.append(dataset)
    subprocess.run(cmd, check=False)


def zfs_create_parent(dataset):
    parent = dataset.rsplit("/", 1)[0]
    if parent:
        subprocess.run(["zfs", "create", "-p", parent], check=False)


def zfs_send_recv(src_snap, dst, recursive=False):
    send_cmd = ["zfs", "send"]
    if recursive:
        send_cmd.append("-R")
    send_cmd.append(src_snap)

    recv_cmd = ["zfs", "receive", dst]

    simple_pipe(send_cmd, recv_cmd)
