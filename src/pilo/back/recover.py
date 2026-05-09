from dataclasses import dataclass

from .. import context
from .. import error
from .. import normalize
from .. import validation
from .. import zfs
from . import restore



@dataclass(frozen=True)
class RecoveryPlan:
    target: str
    replica: str
    snapshot: str
    recursive: bool


def recover_dataset_tree(cx, target, replica, require_new=True):
    plan = build_recovery_plan(cx, target)
    execute_recovery_plan(plan)
    # normalise dataset properties
    normalize.apply_dataset_contract(cx)
    # ensure datasets are mountable and mounted
    zfs.mount()
    # Optional: runtime + ownership (debatable)
    #ensure_runtime_dirs(cx)
    #apply_ownership(cx)


def build_recovery_plan(cx, target):
    mapping = context.DatasetMapping(cx.root_dataset, cx.replica_dataset)

    mapping.validate_within_src(target)
    validation.require_within_dataset(target, cx.root_dataset)

    replica = mapping.map(target)
    validation.require_dataset(replica)

    snap = zfs.latest_snapshot(replica)
    if not snap:
        error.fatal("no snapshots on replica")

    validation.require_snapshot_of_dataset(snap, replica)

    validation.require_new_dataset(target)

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

