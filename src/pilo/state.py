from dataclasses import dataclass, field
from enum import Enum


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
