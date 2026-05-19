from dataclasses import dataclass
from enum import Enum

from .. import checks
from .. import context
from .. import error
from .. import state
from .. import util
from .. import zfs


class ReplicationStatus(Enum):
    OK = "OK"
    EMPTY = "EMPTY"
    BEHIND = "BEHIND"
    DIVERGED = "DIVERGED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReplicationPlan:
    src: str
    dst: str
    snapshot: str
    base: str | None
    mode: str  # "full" | "incremental" | "noop"


def find_incremental_base(src, dst):
    guid = zfs.get_latest_guid(dst)
    if not guid:
        return None
    for name, g in zfs.snapshot_guids(src):
        if g == guid:
            return name
    return None


def replicate(src, dst):
    plan = build_replication_plan(src, dst)
    return execute_replication_plan(plan)


def replication_state(src, dst):

    src_guid = zfs.get_latest_guid(src)
    dst_guid = zfs.get_latest_guid(dst)

    if not src_guid:
        return ReplicationStatus.UNKNOWN, "source has no snapshots"

    if not dst_guid:
        return ReplicationStatus.EMPTY, "replica is uninitialized"

    mapping = context.DatasetMapping(src, dst)

    for dst_ds in zfs.list_filesystems(dst):
        src_ds = mapping.inverse(dst_ds)
        if not zfs.dataset_exists(src_ds):
            return (
                ReplicationStatus.DIVERGED,
                f"orphan replica dataset {dst_ds}",
            )
        base = find_incremental_base(src_ds, dst_ds)
        if not base:
            return ReplicationStatus.DIVERGED, f"divergence in {dst_ds}"

        if zfs.get_latest_guid(src_ds) != zfs.get_latest_guid(dst_ds):
            return ReplicationStatus.BEHIND, f"behind in {dst_ds}"
        # otherwise current

    for src_ds in zfs.list_filesystems(src):
        dst_ds = mapping.map(src_ds)
        if not zfs.dataset_exists(dst_ds):
            return ReplicationStatus.BEHIND, f"missing {dst_ds}"

    return ReplicationStatus.OK, None


# compat
replication_status = replication_state


def build_seed_replication_plan(src, dst):
    checks.require_dataset(src)

    if zfs.latest_snapshot(dst):
        error.fatal("destination already initialized")

    snapshot = checks.require_latest_snapshot(src, "source")

    return ReplicationPlan(
        src=src,
        dst=dst,
        snapshot=snapshot,
        base=None,
        mode="seed",
    )


def build_replica_seed_plan(cx):
    detected = state.detect_lifecycle(cx)

    if not state.lifecycle_seed_replication_permitted(detected):
        error.fatal(
            detected.message or
            "replica seed not permitted in current lifecycle state"
        )

    if not state.lifecycle_has_secondary(detected):
        error.fatal(detected.message or "no secondary available")

    return build_seed_replication_plan(
        cx.root_dataset,
        detected.secondary,
    )


def build_replication_plan(src, dst):

    checks.require_dataset(src)
    checks.require_dataset(dst)

    last_src = checks.require_latest_snapshot(src, "source")
    last_dst = checks.require_latest_snapshot(dst, "destination")

    base = find_incremental_base(src, dst)
    if not base:
        error.fatal(f"base snapshot missing on source: {last_dst}")

    if base == last_src:
        return ReplicationPlan(
            src,
            dst,
            last_src,
            base,
            "noop",
        )
    else:
        return ReplicationPlan(
            src,
            dst,
            last_src,
            base,
            "incremental",
        )


def execute_replication_plan(plan: ReplicationPlan):
    if plan.mode == "seed":
        return zfs.replicate_full(plan.snapshot, plan.dst)

    if plan.mode == "incremental":
        return zfs.replicate_incremental(plan.base, plan.snapshot, plan.dst)

    if plan.mode == "noop":
        return

    error.fatal(f"unrecognized plan mode '{plan.mode}'")
