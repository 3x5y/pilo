from dataclasses import dataclass

from .. import checks
from .. import context
from .. import error
from . import lifecycle
from . import normalize
from . import replay
from . import restore


@dataclass(frozen=True)
class ReplayCatchupPlan:
    replay_batch: replay.BatchReplayPlan
    latest_snapshot: str | None


@dataclass(frozen=True)
class RecoveryPlan:
    target: str
    replica: str
    baseline_snapshot: str
    recursive: bool
    catchup: ReplayCatchupPlan | None = None


def build_recovery_plan(cx, target, stream_dir=None):

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

    catchup = None
    if stream_dir:
        catchup = build_recovery_replay_plan(stream_dir, target, snap)

    return RecoveryPlan(
        target=target,
        replica=replica,
        baseline_snapshot=snap,
        recursive=True,
        catchup=catchup,
    )


def build_recovery_replay_plan(
    stream_dir,
    target_dataset,
    baseline_snapshot,
):
    paths = replay.find_streams(stream_dir)
    if not paths:
        return None

    ordered = replay.order_streams(paths)
    filtered = replay.filter_newer_than(ordered, baseline_snapshot)
    if not filtered:
        return None

    batch = replay.build_batch_replay_plan(filtered, target_dataset)

    from . import snapshot as snapmod
    latest = max(
        (p.manifest.snapshot for p in batch.plans),
        key=lambda s: snapmod.snapshot_sort_key(s),
        default=None,
    )

    return ReplayCatchupPlan(replay_batch=batch, latest_snapshot=latest)


def execute_recovery_plan(plan: RecoveryPlan, cx):
    print(f"RESTORE {plan.baseline_snapshot}")
    restore.restore_dataset(
        plan.baseline_snapshot,
        plan.target,
        recursive=plan.recursive,
    )

    if plan.catchup:
        cnt = len(plan.catchup.replay_batch.plans)
        print(f"REPLAY {cnt} streams")
        for result in replay.execute_batch_replay_plan(plan.catchup.replay_batch):
            print(f"{result.status} {result.snapshot}")

    print("NORMALIZE")
    normalize.normalize_system(cx)

