from dataclasses import dataclass, field
from enum import Enum


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


class ValidationSeverity(Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    component: str | None = None


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)
    lifecycle: LifecycleStatus | None = None

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
    def exit_code(self):
        return 1 if not self.is_healthy else 0

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
        return not self.errors and not self.warnings

    @property
    def highest_severity(self):
        if self.errors:
            return ValidationSeverity.ERROR

        if self.warnings:
            return ValidationSeverity.WARN

        return ValidationSeverity.INFO


def detect_lifecycle(cx):
    from .storage import replication as _replication

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

    repl_state, repl_msg = _replication.replication_status(
        cx.root_dataset,
        secondary.root,
    )

    if repl_state == _replication.ReplicationStatus.OK:
        return LifecycleStatus(
            state=LifecycleState.NORMAL,
            secondary=secondary.root,
        )

    if repl_state == _replication.ReplicationStatus.BEHIND:
        return LifecycleStatus(
            state=LifecycleState.REPLICATION_BEHIND,
            message=repl_msg,
            secondary=secondary.root,
        )

    if repl_state == _replication.ReplicationStatus.DIVERGED:
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
    return ValidationIssue(
        code="lifecycle.state",
        message=lifecycle.state.value,
        severity=ValidationSeverity.INFO,
        component="lifecycle",
    )


def replication_validation_issue(lifecycle):

    if lifecycle.state == LifecycleState.NORMAL:
        return None

    if lifecycle.state == LifecycleState.REPLICA_MISSING:
        return ValidationIssue(
            code="replication.secondary_missing",
            message=lifecycle.message or "secondary missing",
            severity=ValidationSeverity.WARN,
            component="replication",
        )

    if lifecycle.state == LifecycleState.REPLICA_UNINITIALIZED:
        return ValidationIssue(
            code="replication.uninitialized",
            message=lifecycle.message or "secondary uninitialized",
            severity=ValidationSeverity.WARN,
            component="replication",
        )

    if lifecycle.state == LifecycleState.REPLICATION_BEHIND:
        return ValidationIssue(
            code="replication.behind",
            message=lifecycle.message or "replication behind",
            severity=ValidationSeverity.WARN,
            component="replication",
        )

    if lifecycle.state == LifecycleState.REPLICATION_DIVERGED:
        return ValidationIssue(
            code="replication.diverged",
            message=lifecycle.message or "replication diverged",
            severity=ValidationSeverity.ERROR,
            component="replication",
        )

    if lifecycle.state == LifecycleState.INVALID_TOPOLOGY:
        return ValidationIssue(
            code="topology.invalid",
            message=lifecycle.message or "invalid topology",
            severity=ValidationSeverity.ERROR,
            component="replication",
        )

    return ValidationIssue(
        code="replication.unknown",
        message=lifecycle.message or "replication unknown",
        severity=ValidationSeverity.WARN,
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
