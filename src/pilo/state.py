import os
from dataclasses import dataclass, field
from enum import Enum

from . import normalize
from . import util
from . import zfs
from .back import replication


class SystemTopologyState(Enum):
    NORMAL = "NORMAL"
    REPLICA_UNINITIALIZED = "REPLICA_UNINITIALIZED"
    REPLICA_MISSING = "REPLICA_MISSING"
    REPLICATION_BEHIND = "REPLICATION_BEHIND"
    REPLICATION_DIVERGED = "REPLICATION_DIVERGED"
    INVALID_TOPOLOGY = "INVALID_TOPOLOGY"
    UNKNOWN = "UNKNOWN"


class ValidationSeverity(Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass(frozen=True)
class DetectedSystemState:
    state: SystemTopologyState
    message: str | None = None
    secondary: str | None = None


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    component: str | None = None


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    def extend(self, issues):
        self.issues.extend(issues)

    def by_code(self, code):
        return [
            i for i in self.issues
            if i.code == code
        ]

    def by_component(self, component):
        return [
            i for i in self.issues
            if i.component == component
        ]

    @property
    def has_errors(self):
        return any(
            i.severity == ValidationSeverity.ERROR
            for i in self.issues
        )

    @property
    def warnings(self):
        return [
            i for i in self.issues
            if i.severity == ValidationSeverity.WARN
        ]

    @property
    def errors(self):
        return [
            i for i in self.issues
            if i.severity == ValidationSeverity.ERROR
        ]

    @property
    def is_healthy(self):
        return not self.issues

    @property
    def highest_severity(self):
        if self.errors:
            return ValidationSeverity.ERROR

        if self.warnings:
            return ValidationSeverity.WARN

        return ValidationSeverity.INFO


def detect_system_state(cx):

    try:
        secondary = cx.current_secondary_state
    except RuntimeError as e:
        return DetectedSystemState(
            state=SystemTopologyState.INVALID_TOPOLOGY,
            message=str(e),
        )

    if not secondary:
        return DetectedSystemState(
            state=SystemTopologyState.REPLICA_MISSING,
            message="no secondary configured",
        )

    if not secondary.carrier_attached:
        return DetectedSystemState(
            state=SystemTopologyState.REPLICA_MISSING,
            message=f"secondary unattached: {secondary.root}",
            secondary=secondary.root,
        )

    if not secondary.dataset_exists:
        return DetectedSystemState(
            state=SystemTopologyState.REPLICA_UNINITIALIZED,
            message=f"secondary dataset missing: {secondary.root}",
            secondary=secondary.root,
        )

    if not secondary.initialized:
        return DetectedSystemState(
            state=SystemTopologyState.REPLICA_UNINITIALIZED,
            message=f"secondary uninitialized: {secondary.root}",
            secondary=secondary.root,
        )

    repl_state, repl_msg = replication.replication_status(
        cx.root_dataset,
        secondary.root,
    )

    if repl_state == replication.ReplicationStatus.OK:
        return DetectedSystemState(
            state=SystemTopologyState.NORMAL,
            secondary=secondary.root,
        )

    if repl_state == replication.ReplicationStatus.BEHIND:
        return DetectedSystemState(
            state=SystemTopologyState.REPLICATION_BEHIND,
            message=repl_msg,
            secondary=secondary.root,
        )

    if repl_state == replication.ReplicationStatus.DIVERGED:
        return DetectedSystemState(
            state=SystemTopologyState.REPLICATION_DIVERGED,
            message=repl_msg,
            secondary=secondary.root,
        )

    return DetectedSystemState(
        state=SystemTopologyState.UNKNOWN,
        message=repl_msg,
        secondary=secondary.root,
    )


def collect_dataset_validation(cx):
    return normalize.validate_dataset_contracts(cx)


def collect_validation_report(cx, include=None):
    if include is None:
        include = {"datasets", "snapshot", "replication"}

    report = ValidationReport()

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
            os.environ.get(
                "CONFIG_SNAPSHOT_MAX_AGE",
                "3600",
            )
        )
    if not name:
        issues.append(
            ValidationIssue(
                code="snapshot.missing",
                message=f"none for {dataset}",
                severity=ValidationSeverity.WARN,
                component="snapshot",
            )
        )
        return issues
    if ts is None:
        issues.append(
            ValidationIssue(
                code="snapshot.invalid_timestamp",
                message="could not parse timestamp",
                severity=ValidationSeverity.WARN,
                component="snapshot",
            )
        )
        return issues

    age = util.now_epoch() - ts
    if age > max_age:
        issues.append(
            ValidationIssue(
                code="snapshot.stale",
                message=f"stale ({age} s)",
                severity=ValidationSeverity.WARN,
                component="snapshot",
            )
        )
    return issues


def collect_replication_validation(cx):

    issues = []

    detected = detect_system_state(cx)

    if detected.state == SystemTopologyState.NORMAL:
        return issues

    if detected.state == SystemTopologyState.REPLICA_MISSING:
        issues.append(
            ValidationIssue(
                code="replication.secondary_missing",
                message=detected.message or "secondary missing",
                severity=ValidationSeverity.WARN,
                component="replication",
            )
        )
        return issues

    if detected.state == SystemTopologyState.REPLICA_UNINITIALIZED:
        issues.append(
            ValidationIssue(
                code="replication.uninitialized",
                message=detected.message or "secondary uninitialized",
                severity=ValidationSeverity.WARN,
                component="replication",
            )
        )
        return issues

    if detected.state == SystemTopologyState.REPLICATION_BEHIND:
        issues.append(
            ValidationIssue(
                code="replication.behind",
                message=detected.message or "replication behind",
                severity=ValidationSeverity.WARN,
                component="replication",
            )
        )
        return issues

    if detected.state == SystemTopologyState.REPLICATION_DIVERGED:
        issues.append(
            ValidationIssue(
                code="replication.diverged",
                message=detected.message or "replication diverged",
                severity=ValidationSeverity.ERROR,
                component="replication",
            )
        )
        return issues

    if detected.state == SystemTopologyState.INVALID_TOPOLOGY:
        issues.append(
            ValidationIssue(
                code="topology.invalid",
                message=detected.message or "invalid topology",
                severity=ValidationSeverity.ERROR,
                component="replication",
            )
        )
        return issues

    issues.append(
        ValidationIssue(
            code="replication.unknown",
            message=detected.message or "replication unknown",
            severity=ValidationSeverity.WARN,
            component="replication",
        )
    )

    return issues
