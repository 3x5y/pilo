from dataclasses import dataclass
import os
import subprocess

from . import fs
from . import git
from . import state
from . import util
from . import zfs


def render_validation_issue(issue):
    return (
        f"{issue.severity.value}: "
        f"{issue.code}: "
        f"{issue.message}"
    )


def render_validation_report(report):
    return [render_validation_issue(i) for i in report.issues]


def collect_transient_validation(cx):
    issues = []
    for git_dir in cx.admin_path.rglob(".git"):
        repo = git_dir.parent
        if git.is_dirty(repo):
            i = state.ValidationIssue(
                code="transient.state",
                message=f"repo {repo} has uncommitted changes",
                severity=state.ValidationSeverity.WARN,
                component="transient",
            )
            issues.append(i)
    return issues


def collect_pile_validation(cx):
    pile = cx.pile_path
    if not pile.exists():
        return []

    now = util.now_epoch()
    max_age = int(os.environ.get("CONFIG_PILE_MAX_AGE", "86400"))

    issues = []
    for f in fs.iter_files(pile):
        age = now - int(f.stat().st_mtime)
        if age > max_age:
            i = state.ValidationIssue(
                code="pile.state",
                message=f"{f} is older than threshold",
                severity=state.ValidationSeverity.WARN,
                component="pile",
            )
            issues.append(i)
    return issues


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


def collect_manifest_validation(cx):
    issues = []
    for subset in ("pile", "collection", "filing"):
        i = check_manifest(cx, subset)
        if i:
            issues.append(i)
    return issues


def check_manifest(cx, subset):
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
        return state.ValidationIssue(
                code="manifest.state",
                message=f"{subset} verified",
                severity=state.ValidationSeverity.INFO,
                component="manifest",
            )
    except subprocess.CalledProcessError:
        return state.ValidationIssue(
                code="manifest.state",
                message=f"{subset} verification failed",
                severity=state.ValidationSeverity.ERROR,
                component="manifest",
            )


def collect_report(cx, check=None):

    include = {"datasets", "snapshot", "replication" }
    if check is not None:
        include = {check}

    report = state.collect_validation_report(cx, include=include)

    if check in (None, "transient"):
        report.extend(collect_transient_validation(cx))

    if check in (None, "pile"):
        report.extend(collect_pile_validation(cx))

    if check in (None, "manifest"):
        report.extend(collect_manifest_validation(cx))

    return report


