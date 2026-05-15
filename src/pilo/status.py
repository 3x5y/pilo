from dataclasses import dataclass
import os
import subprocess

from . import fs
from . import git
from . import normalize
from . import util
from . import zfs


@dataclass(frozen=True)
class StatusMessage:
    level: str
    category: str
    message: str


@dataclass
class SystemStatus:
    messages: list[StatusMessage] = None
    code: int = 0

    def __post_init__(self):
        if self.messages is None:
            self.messages = []

    def warn(self, category, msg):
        sm = StatusMessage("WARN", category, msg)
        self.messages.append(sm)
        self.code = 1

    def ok(self, category, msg):
        sm = StatusMessage("OK", category, msg)
        self.messages.append(sm)


@dataclass(frozen=True)
class StatusCheck:
    name: str
    func_name: str

    @property
    def func(self):
        return globals()[self.func_name]


class status_checks:
    ALL = [
        StatusCheck("transient", "check_transient_status"),
        StatusCheck("pile", "check_pile_status"),
        StatusCheck("snapshot", "check_snapshot_status"),
        StatusCheck("replication", "check_replication_status"),
        StatusCheck("datasets", "check_dataset_status"),
        StatusCheck("manifest", "check_manifest_status"),
    ]

    @staticmethod
    def lookup(name):
        for check in status_checks.ALL:
            if check.name == name:
                return check
        return None


def render_status_message(msg):
    return f"{msg.level}: {msg.category}: {msg.message}"


def render_system_status(st):
    return [render_status_message(m) for m in st.messages]


def check_replication_status(cx, st: SystemStatus):
    src = cx.root_dataset
    dst = cx.replica_dataset

    src_snap = zfs.latest_snapshot(src)
    dst_snap = zfs.latest_snapshot(dst)

    src_name = src_snap.split("@", 1)[1] if src_snap else "**MISSING**"
    dst_name = dst_snap.split("@", 1)[1] if dst_snap else "**MISSING**"

    if src_name != dst_name:
        st.warn("replication", f"latest={src_name} replicated={dst_name}")
    else:
        st.ok("replication", src_name)


def check_snapshot_status(cx, st: SystemStatus, max_age=None):
    dataset = cx.pile_dataset

    name, ts = zfs.latest_snapshot_with_time(dataset)
    if max_age is None:
        max_age = int(os.environ.get("CONFIG_SNAPSHOT_MAX_AGE", "3600"))

    if not name:
        st.warn("snapshot", f"none for {dataset}")
        return

    if ts is None:
        st.warn("snapshot", "could not parse timestamp")
        return

    age = util.now_epoch() - ts

    if age > max_age:
        st.warn("snapshot", f"stale ({age} s)")
    else:
        st.ok("snapshot", f"fresh ({age} s)")


def check_dataset_status(cx, st: SystemStatus):
    required = [
        cx.admin_dataset,
        cx.intake_dataset,
        cx.pile_dataset,
        f"{cx.static_dataset}/collection",
    ]

    for ds in required:
        if not zfs.dataset_exists(ds):
            st.warn("incomplete", f"missing dataset {ds}")


def check_dataset_status(cx, st: SystemStatus):
    issues = normalize.validate_dataset_contracts(cx)
    for issue in issues:
        st.warn(issue.code, issue.message)
    if not issues:
        st.ok("datasets", "all dataset contracts satisfied")


def check_transient_status(cx, st: SystemStatus):
    for git_dir in cx.admin_path.rglob(".git"):
        repo = git_dir.parent
        if git.is_dirty(repo):
            st.warn("transient", f"repo {repo} has uncommitted changes")


def check_pile_status(cx, st: SystemStatus):
    pile = cx.pile_path
    if not pile.exists():
        return

    now = util.now_epoch()
    max_age = int(os.environ.get("CONFIG_PILE_MAX_AGE", "86400"))

    for f in fs.iter_files(pile):
        age = now - int(f.stat().st_mtime)
        if age > max_age:
            st.warn("pile", f"{f} is older than threshold")


def check_manifest_status(cx, st):
    for subset in ("pile", "collection", "filing"):
        collect_manifest_status(cx, st, subset)


def collect_system_status(cx, check=None):
    st = SystemStatus()
    for entry in status_checks.ALL:
        if check is None or check == entry.name:
            entry.func(cx, st)
    return st


def collect_manifest_status(cx, st, subset):
    if subset == 'pile':
        base_dir = cx.pile_path
    elif subset in ('collection', 'filing'):
        base_dir = cx.static_path / subset
    else:
        raise Exception(f"Unsupported subset '{subset}'")

    manifest = cx.admin_path / "manifest" / f"{subset}.manifest"

    if (not manifest.is_file() or manifest.stat().st_size == 0):
        return

    try:
        cmd = ["sha256sum", "--quiet", "--strict", "-c", manifest]
        subprocess.run(cmd, cwd=str(base_dir), check=True)
        st.ok("manifest", f"{subset} verified")
    except subprocess.CalledProcessError:
        st.warn("manifest", f"{subset} verification failed")
