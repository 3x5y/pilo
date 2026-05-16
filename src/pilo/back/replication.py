from dataclasses import dataclass
from enum import Enum

from .. import checks
from .. import context
from .. import error
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


def replication_status(src, dst):
    src_guid = zfs.get_latest_guid(src)
    dst_guid = zfs.get_latest_guid(dst)

    if not dst_guid:
        return ReplicationStatus.EMPTY, "no snapshots on target"

    mapping = context.DatasetMapping(src, dst)

    for dst_ds in zfs.list_filesystems(dst):
        src_ds = mapping.inverse(dst_ds)

        src_guids = set(zfs.list_guids(src_ds))
        dst_guids = set(zfs.list_guids(dst_ds))

        if dst_guids - src_guids:
            return ReplicationStatus.DIVERGED, f"divergence in {dst_ds}"

        if zfs.get_latest_guid(src_ds) != zfs.get_latest_guid(dst_ds):
            return ReplicationStatus.BEHIND, f"behind in {dst_ds}"

    for src_ds in zfs.list_filesystems(src):
        dst_ds = mapping.map(src_ds)
        if not zfs.dataset_exists(dst_ds):
            return ReplicationStatus.BEHIND, f"missing {dst_ds}"

    if src_guid != dst_guid:
        return ReplicationStatus.UNKNOWN, "root GUID mismatch"

    return ReplicationStatus.OK, None


def build_replication_plan(src, dst):
    last_src = zfs.latest_snapshot(src)
    last_dst = zfs.latest_snapshot(dst)

    if not last_src:
        error.fatal("no source snapshot")

    checks.require_dataset(src)
    if not last_dst:
        return ReplicationPlan( src, dst, last_src, None, "full")

    base = find_incremental_base(src, dst)

    if not base:
        error.fatal(f"base snapshot missing on source: {base}")

    if base == last_src:
        return ReplicationPlan(src, dst, last_src, base, "noop")

    return ReplicationPlan(src, dst, last_src, base, "incremental")


def execute_replication_plan(plan: ReplicationPlan):
    if plan.mode == "full":
        return zfs.replicate_full(plan.snapshot, plan.dst)

    if plan.mode == "incremental":
        return zfs.replicate_incremental(plan.base, plan.snapshot, plan.dst)

    if plan.mode == "noop":
        return
