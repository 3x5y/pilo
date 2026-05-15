from dataclasses import dataclass, field
from enum import Enum

from . import normalize
from . import status as status_mod
from .back import replication


class OperationalState(Enum):
    HEALTHY = "HEALTHY"
    INCOMPLETE = "INCOMPLETE"
    STALE_SNAPSHOTS = "STALE_SNAPSHOTS"
    REPLICATION_BEHIND = "REPLICATION_BEHIND"
    REPLICATION_DIVERGED = "REPLICATION_DIVERGED"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True)
class StateIssue:
    code: str
    message: str


@dataclass
class SystemState:
    state: OperationalState
    issues: list[StateIssue] = field(default_factory=list)


def derive_operational_state(cx):
    issues = []
    contract_issues = normalize.validate_dataset_contracts(cx)
    if contract_issues:
        return SystemState(
            state=OperationalState.INCOMPLETE,
            issues=[
                StateIssue(i.code, i.message)
                for i in contract_issues
            ],
        )
    repl_state, repl_msg = replication.replication_status(
        cx.root_dataset,
        cx.replica_dataset,
    )
    if repl_state == replication.ReplicationStatus.DIVERGED:
        return SystemState(
            state=OperationalState.REPLICATION_DIVERGED,
            issues=[
                StateIssue(
                    "replication.diverged",
                    repl_msg or "replication diverged",
                )
            ],
        )
    if repl_state in (
        replication.ReplicationStatus.BEHIND,
        replication.ReplicationStatus.EMPTY,
    ):
        issues.append(
            StateIssue(
                "replication.behind",
                repl_msg or "replication behind",
            )
        )

    st = status_mod.SystemStatus()
    status_mod.check_snapshot_status(cx, st)

    if st.code != 0:
        issues.append(
            StateIssue(
                "snapshot.stale",
                "snapshot freshness violation",
            )
        )

    if issues:
        return SystemState(
            state=OperationalState.DEGRADED,
            issues=issues,
        )
    return SystemState(
        state=OperationalState.HEALTHY,
    )
