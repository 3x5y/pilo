from dataclasses import dataclass

from .. import checks
from .. import context
from .. import error
from . import lifecycle
from . import normalize
from . import restore


@dataclass(frozen=True)
class RecoveryPlan:
    target: str
    replica: str
    baseline_snapshot: str
    recursive: bool


def build_recovery_plan(cx, target):

    detected = lifecycle.detect_lifecycle(cx)

    if not lifecycle.lifecycle_recovery_permitted(detected):
        error.fatal(
            detected.message or
            "recovery not permitted in current lifecycle state"
        )

    if not lifecycle.lifecycle_has_secondary(detected):
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
        baseline_snapshot=snap,
        recursive=True,
    )


def execute_recovery_plan(plan: RecoveryPlan, cx):
    print(f"RESTORE {plan.baseline_snapshot}")
    restore.restore_dataset(
        plan.baseline_snapshot,
        plan.target,
        recursive=plan.recursive,
    )

    print("NORMALIZE")
    normalize.normalize_system(cx)

