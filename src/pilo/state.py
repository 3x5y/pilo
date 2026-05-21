from . import util
from . import zfs
from .back import normalize
from .lifecycle import (
    ValidationIssue,
    ValidationSeverity,
    ValidationReport,
    detect_lifecycle,
    lifecycle_validation_issue,
    replication_validation_issue,
)


def collect_dataset_validation(cx):
    return normalize.validate_dataset_contracts(cx)


def collect_validation_report(cx, include=None):
    if include is None:
        include = {"datasets", "snapshot", "replication"}

    lifecycle = detect_lifecycle(cx)
    report = ValidationReport(lifecycle=lifecycle)
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
    lifecycle = detect_lifecycle(cx)
    issue = replication_validation_issue(lifecycle)
    if issue is None:
        return []
    return [issue]
