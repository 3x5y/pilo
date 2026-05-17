from dataclasses import dataclass
import os
import subprocess

from . import fs
from . import git
from . import state
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


def render_status_message(msg):
    return f"{msg.level}: {msg.category}: {msg.message}"


def render_system_status(st):
    return [render_status_message(m) for m in st.messages]


def validation_issue_to_status_message(issue):
    return StatusMessage(
        level=issue.severity.value,
        category=issue.code,
        message=issue.message,
    )


def validation_report_to_status_messages(report):
    return [validation_issue_to_status_message(i)
            for i in report.issues]


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


def collect_system_status(cx, check=None):

    include = {"datasets", "snapshot", "replication" }
    if check is not None:
        include = {check}

    report = state.collect_validation_report(cx, include=include)
    system_state = state.derive_operational_state(cx, report=report)
    st = SystemStatus()
    st.messages.extend(validation_report_to_status_messages(report))
    st.messages.append(
        StatusMessage(
            level="INFO",
            category="state",
            message=system_state.state.name,
        )
    )

    if report.issues:
        st.code = 1

    if check in (None, "transient"):
        check_transient_status(cx, st)

    if check in (None, "pile"):
        check_pile_status(cx, st)

    if check in (None, "manifest"):
        check_manifest_status(cx, st)

    return st
