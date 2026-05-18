from dataclasses import dataclass

from .. import checks
from .. import context
from .. import error
from .. import normalize
from .. import state
from . import restore



@dataclass(frozen=True)
class RecoveryPlan:
    target: str
    replica: str
    snapshot: str
    recursive: bool


def build_recovery_plan(cx, target):

    detected = state.detect_lifecycle(cx)

    if not state.lifecycle_recoverable(detected):
        error.fatal(
            detected.message or
            "recovery not permitted in current lifecycle state"
        )

    if detected.secondary is None:
        error.fatal(detected.message or "no secondary available")

    secondary = detected.secondary

    mapping = context.DatasetMapping(cx.root_dataset, secondary)
    mapping.validate_within_src(target)
    checks.require_within_dataset(target, cx.root_dataset)

    replica = mapping.map(target)
    checks.require_dataset(replica)

    snap = checks.require_latest_snapshot(replica, "replica")
    checks.require_snapshot_of_dataset(snap, replica)

    checks.require_new_dataset(target)

    return RecoveryPlan(
        target=target,
        replica=replica,
        snapshot=snap,
        recursive=True,
    )


def execute_recovery_plan(plan: RecoveryPlan, cx):
    restore.restore_dataset(
        plan.snapshot,
        plan.target,
        recursive=plan.recursive,
    )
    normalize.normalize_system(cx)

