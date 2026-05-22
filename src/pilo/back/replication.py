from dataclasses import dataclass
from enum import Enum

from .. import checks
from .. import context
from .. import error
from .. import lifecycle
from .. import util
from .. import zfs
from . import continuity


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
    mode: str
    hold_snapshot: str | None = None
    hold_tag: str | None = None
    export_path: str | None = None


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

    # existence/snapshot sanity check
    src_latest = zfs.get_latest_guid(src)
    dst_latest = zfs.get_latest_guid(dst)

    if not src_latest:
        return ReplicationStatus.UNKNOWN, "source has no snapshots"

    if not dst_latest:
        # existing destination dataset with no snapshots:
        # unusable replication sink under append-only policy
        return ReplicationStatus.EMPTY, "replica is uninitialized"

    mapping = context.DatasetMapping(src, dst)

    # authoritative continuity validation:
    # every replica dataset must map to a valid source dataset
    # and preserve incremental continuity
    for dst_ds in zfs.list_filesystems(dst):
        src_ds = mapping.inverse(dst_ds)
        if not zfs.dataset_exists(src_ds):
            continue
            #return (
            #    ReplicationStatus.DIVERGED,
            #    f"orphan replica dataset {dst_ds}",
            #)
        base = find_incremental_base(src_ds, dst_ds)
        if not base:
            return ReplicationStatus.DIVERGED, f"divergence in {dst_ds}"

        if zfs.get_latest_guid(src_ds) != zfs.get_latest_guid(dst_ds):
            return ReplicationStatus.BEHIND, f"behind in {dst_ds}"
        # otherwise current

    # authoritative structural completeness validation:
    # every source dataset must exist on replica
    for src_ds in zfs.list_filesystems(src):
        dst_ds = mapping.map(src_ds)
        if not zfs.dataset_exists(dst_ds):
            return ReplicationStatus.BEHIND, f"missing {dst_ds}"

    return ReplicationStatus.OK, None


# compat
replication_status = replication_state


def _has_continuity_hold(snapshot, label):
    tag = continuity.hold_tag(label)
    for _, t in zfs.list_holds(snapshot):
        if t == tag:
            return True
    return False


def build_seed_replication_plan(src, dst, label=None):
    checks.require_dataset(src)

    if zfs.latest_snapshot(dst):
        error.fatal("destination already initialized")

    snapshot = checks.require_latest_snapshot(src, "source")

    hold = snapshot if label else None
    tag = continuity.hold_tag(label) if label else None

    return ReplicationPlan(
        src=src,
        dst=dst,
        snapshot=snapshot,
        base=None,
        mode="seed",
        hold_snapshot=hold,
        hold_tag=tag,
    )


def build_replica_seed_plan(cx):
    detected = lifecycle.detect_lifecycle(cx)

    if not lifecycle.lifecycle_seed_replication_permitted(detected):
        error.fatal(
            detected.message or
            "replica seed not permitted in current lifecycle state"
        )

    if not lifecycle.lifecycle_has_secondary(detected):
        error.fatal(detected.message or "no secondary available")

    label = continuity.label_for_secondary(cx, detected.secondary)

    return build_seed_replication_plan(
        cx.root_dataset,
        detected.secondary,
        label=label,
    )


def build_replication_plan(src, dst, label=None):

    checks.require_dataset(src)
    checks.require_dataset(dst)

    last_src = checks.require_latest_snapshot(src, "source")
    last_dst = checks.require_latest_snapshot(dst, "destination")

    base = find_incremental_base(src, dst)
    if not base:
        error.fatal(f"base snapshot missing on source: {last_dst}")

    if base == last_src:
        mode = "noop"
    else:
        mode = "incremental"

    hold_snap = None
    hold_t = None
    if label is not None:
        if mode == "noop":
            if not _has_continuity_hold(last_src, label):
                error.fatal(
                    f"replica current but continuity hold missing "
                    f"on {last_src}"
                )
        else:
            hold_snap = last_src
            hold_t = continuity.hold_tag(label)

    return ReplicationPlan(
        src, dst, last_src, base, mode,
        hold_snapshot=hold_snap,
        hold_tag=hold_t,
    )


def execute_replication_plan(plan: ReplicationPlan):
    if plan.hold_snapshot and plan.hold_tag:
        zfs.hold(plan.hold_tag, plan.hold_snapshot)

    if plan.mode == "seed":
        return zfs.replicate_full(plan.snapshot, plan.dst,
                                  tee_path=plan.export_path)

    if plan.mode == "incremental":
        return zfs.replicate_incremental(plan.base, plan.snapshot, plan.dst,
                                         tee_path=plan.export_path)

    if plan.mode == "noop":
        return

    error.fatal(f"unrecognized plan mode '{plan.mode}'")
