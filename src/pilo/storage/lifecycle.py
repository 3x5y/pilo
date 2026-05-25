from dataclasses import dataclass, field
from enum import Enum

from .. import state
from .. import util
from .. import zfs
from . import normalize
from . import replication


class LifecycleState(Enum):
    NORMAL = "NORMAL"
    REPLICA_MISSING = "REPLICA_MISSING"
    REPLICA_UNINITIALIZED = "REPLICA_UNINITIALIZED"
    REPLICATION_BEHIND = "REPLICATION_BEHIND"
    REPLICATION_DIVERGED = "REPLICATION_DIVERGED"
    INVALID_TOPOLOGY = "INVALID_TOPOLOGY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class LifecycleStatus:
    state: LifecycleState
    message: str | None = None
    secondary: str | None = None


def detect_lifecycle(cx):

    try:
        secondary = cx.current_secondary_state
    except RuntimeError as e:
        return LifecycleStatus(
            state=LifecycleState.INVALID_TOPOLOGY,
            message=str(e),
        )

    if not secondary:
        return LifecycleStatus(
            state=LifecycleState.REPLICA_MISSING,
            message="no secondary configured",
        )

    if not secondary.carrier_attached:
        return LifecycleStatus(
            state=LifecycleState.REPLICA_MISSING,
            message=f"secondary unattached: {secondary.root}",
            secondary=secondary.root,
        )

    if not secondary.dataset_exists:
        return LifecycleStatus(
            state=LifecycleState.REPLICA_UNINITIALIZED,
            message=f"secondary dataset missing: {secondary.root}",
            secondary=secondary.root,
        )

    if not secondary.initialized:
        return LifecycleStatus(
            state=LifecycleState.REPLICA_UNINITIALIZED,
            message=f"secondary uninitialized: {secondary.root}",
            secondary=secondary.root,
        )

    repl_state, repl_msg = replication.replication_status(
        cx.root_dataset,
        secondary.root,
    )

    if repl_state == replication.ReplicationStatus.OK:
        return LifecycleStatus(
            state=LifecycleState.NORMAL,
            secondary=secondary.root,
        )

    if repl_state == replication.ReplicationStatus.BEHIND:
        return LifecycleStatus(
            state=LifecycleState.REPLICATION_BEHIND,
            message=repl_msg,
            secondary=secondary.root,
        )

    if repl_state == replication.ReplicationStatus.DIVERGED:
        return LifecycleStatus(
            state=LifecycleState.REPLICATION_DIVERGED,
            message=repl_msg,
            secondary=secondary.root,
        )

    return LifecycleStatus(
        state=LifecycleState.UNKNOWN,
        message=repl_msg,
        secondary=secondary.root,
    )


def lifecycle_validation_issue(lifecycle):
    return state.ValidationIssue(
        code="lifecycle.state",
        message=lifecycle.state.value,
        severity=state.ValidationSeverity.INFO,
        component="lifecycle",
    )


def replication_validation_issue(lifecycle):

    if lifecycle.state == LifecycleState.NORMAL:
        return None

    if lifecycle.state == LifecycleState.REPLICA_MISSING:
        return state.ValidationIssue(
            code="replication.secondary_missing",
            message=lifecycle.message or "secondary missing",
            severity=state.ValidationSeverity.WARN,
            component="replication",
        )

    if lifecycle.state == LifecycleState.REPLICA_UNINITIALIZED:
        return state.ValidationIssue(
            code="replication.uninitialized",
            message=lifecycle.message or "secondary uninitialized",
            severity=state.ValidationSeverity.WARN,
            component="replication",
        )

    if lifecycle.state == LifecycleState.REPLICATION_BEHIND:
        return state.ValidationIssue(
            code="replication.behind",
            message=lifecycle.message or "replication behind",
            severity=state.ValidationSeverity.WARN,
            component="replication",
        )

    if lifecycle.state == LifecycleState.REPLICATION_DIVERGED:
        return state.ValidationIssue(
            code="replication.diverged",
            message=lifecycle.message or "replication diverged",
            severity=state.ValidationSeverity.ERROR,
            component="replication",
        )

    if lifecycle.state == LifecycleState.INVALID_TOPOLOGY:
        return state.ValidationIssue(
            code="topology.invalid",
            message=lifecycle.message or "invalid topology",
            severity=state.ValidationSeverity.ERROR,
            component="replication",
        )

    return state.ValidationIssue(
        code="replication.unknown",
        message=lifecycle.message or "replication unknown",
        severity=state.ValidationSeverity.WARN,
        component="replication",
    )


def lifecycle_has_secondary(lifecycle):
    return lifecycle.state not in {
        LifecycleState.REPLICA_MISSING,
        LifecycleState.INVALID_TOPOLOGY,
    }


def lifecycle_replication_healthy(lifecycle):
    return lifecycle.state == LifecycleState.NORMAL


def lifecycle_replication_degraded(lifecycle):
    return lifecycle.state in {
        LifecycleState.REPLICATION_BEHIND,
        LifecycleState.REPLICATION_DIVERGED,
    }


def lifecycle_recoverable(lifecycle):
    return lifecycle.state in {
        LifecycleState.NORMAL,
        LifecycleState.REPLICATION_BEHIND,
        LifecycleState.REPLICATION_DIVERGED,
    }


def lifecycle_replication_permitted(lifecycle):
    return lifecycle.state in {
        LifecycleState.NORMAL,
        LifecycleState.REPLICATION_BEHIND,
    }


def lifecycle_recovery_permitted(lifecycle):
    return lifecycle.state in {
        LifecycleState.NORMAL,
        LifecycleState.REPLICATION_BEHIND,
        LifecycleState.REPLICATION_DIVERGED,
        LifecycleState.UNKNOWN,
    }


def lifecycle_validation_permitted(lifecycle):
    return lifecycle.state != LifecycleState.INVALID_TOPOLOGY


def lifecycle_seed_replication_permitted(lifecycle):
    return lifecycle.state in {
        LifecycleState.REPLICA_UNINITIALIZED,
    }


def lifecycle_requires_provisioning(lifecycle):
    return lifecycle.state == LifecycleState.REPLICA_UNINITIALIZED


def lifecycle_has_replication_fault(lifecycle):
    return lifecycle.state in {
        LifecycleState.REPLICATION_BEHIND,
        LifecycleState.REPLICATION_DIVERGED,
        LifecycleState.UNKNOWN,
    }


def collect_dataset_validation(cx):
    return normalize.validate_dataset_contracts(cx)


def collect_validation_report(cx, include=None):
    if include is None:
        include = {"datasets", "snapshot", "replication"}

    lifecycle = detect_lifecycle(cx)
    report = state.ValidationReport(lifecycle=lifecycle)
    report.extend([
        lifecycle_validation_issue(lifecycle)
    ])

    if "datasets" in include:
        report.extend(collect_dataset_validation(cx))

    if "snapshot" in include:
        report.extend(collect_snapshot_validation(cx))

    if "replication" in include:
        report.extend(collect_replication_validation(cx))

    return report


def collect_snapshot_validation(cx, max_age=None):

    issues = []
    dataset = cx.pile_dataset
    name, ts = zfs.latest_snapshot_with_time(dataset)
    if max_age is None:
        max_age = int(
            __import__("os").environ.get(
                "CONFIG_SNAPSHOT_MAX_AGE",
                "3600",
            )
        )
    if not name:
        issues.append(
            state.ValidationIssue(
                code="snapshot.missing",
                message=f"none for {dataset}",
                severity=state.ValidationSeverity.WARN,
                component="snapshot",
            )
        )
        return issues
    if ts is None:
        issues.append(
            state.ValidationIssue(
                code="snapshot.invalid_timestamp",
                message="could not parse timestamp",
                severity=state.ValidationSeverity.WARN,
                component="snapshot",
            )
        )
        return issues

    age = util.now_epoch() - ts
    if age > max_age:
        issues.append(
            state.ValidationIssue(
                code="snapshot.stale",
                message=f"stale ({age} s)",
                severity=state.ValidationSeverity.WARN,
                component="snapshot",
            )
        )
    return issues


def collect_replication_validation(cx):
    lifecycle = detect_lifecycle(cx)
    issue = replication_validation_issue(lifecycle)
    if issue is None:
        return []
    return [issue]
