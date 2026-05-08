from dataclasses import dataclass

from .. import error
from .. import validation
from .. import zfs


@dataclass(frozen=True)
class RestorePlan:
    src_snapshot: str
    dst: str
    recursive: bool


def restore_dataset(src_snap, dst, recursive=False, require_new=True):
    validation.require_snapshot(src_snap)

    if require_new:
        validation.require_new_dataset(dst)

    zfs.send_recv(src_snap, dst, recursive=recursive)

    snap_name = src_snap.split("@", 1)[1]
    if not zfs.snapshot_exists(f"{dst}@{snap_name}"):
        error.fatal("restore completed but snapshot missing at destination")


def build_restore_plan(src, dst, snap, recursive):
    if "@" in snap:
        error.fatal("snapshot must not include dataset")
    src_snap = f"{src}@{snap}"
    validation.require_snapshot(src_snap)
    validation.require_snapshot_of_dataset(src_snap, src)
    validation.require_new_dataset(dst)
    return RestorePlan(
        src_snapshot=src_snap,
        dst=dst,
        recursive=recursive,
    )


def execute_restore_plan(plan: RestorePlan):
    restore_dataset(
        plan.src_snapshot,
        plan.dst,
        recursive=plan.recursive,
    )


