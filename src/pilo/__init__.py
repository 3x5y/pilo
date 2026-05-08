import filecmp
import hashlib
import os
import pwd
import shutil
import subprocess
import sys
import tempfile
from contextlib import ExitStack
from datetime import datetime
from enum import Enum

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from . import zfs

from .context import *
from .error import *
from .fs import *
from .manifest import *
from .mutation import *
from .paths import *
from .status import *
from .util import *
from .validation import *
from .front.rewrite import *


#####################
#    init stuff     #
#####################


def apply_dataset_contract(cx):

    apply_namespace(cx.root_dataset + '/active')
    apply_filesystem(cx.root_dataset + '/active/admin',
                     readonly=False,
                     mountpoint=cx.admin_path)
    apply_filesystem(cx.root_dataset + '/active/pile-intake',
                     readonly=False,
                     mountpoint=cx.intake_path)
    apply_filesystem(cx.root_dataset + '/active/pile-readonly',
                     readonly=True,
                     mountpoint=cx.pile_path)

    apply_namespace(cx.root_dataset + '/static')
    apply_filesystem(cx.root_dataset + '/static/collection',
                     readonly=True,
                     mountpoint=cx.collection_path)

    apply_namespace(cx.root_dataset + '/static/filing',
                    mountpoint=cx.filing_path)


def apply_namespace(ds, mountpoint=None):
    require_dataset(ds)
    mp = zfs.get_prop(ds, 'mountpoint')
    if mountpoint and mp != str(mountpoint):
        zfs.set_prop(ds, f"mountpoint={mountpoint}")
    zfs.set_prop(ds, "canmount=off")


def apply_filesystem(ds, mountpoint, readonly):
    require_dataset(ds)
    zfs.set_readonly(ds, readonly)
    mp = zfs.get_prop(ds, 'mountpoint')
    if mp != str(mountpoint):
        zfs.set_prop(ds, f"mountpoint={mountpoint}")
    zfs.set_prop(ds, "canmount=on")


def ensure_runtime_dirs(cx):
    pile = cx.pile_path
    with dataset_writable(cx.pile_dataset):
        cx.ensure_dir(pile / "in")
        cx.ensure_dir(pile / "sort")
        cx.ensure_dir(pile / "out")
        cx.ensure_dir(pile / "out" / "collection")
        cx.ensure_dir(pile / "out" / "filing")


def apply_ownership(cx):
    cx.ensure_owned(cx.admin_path)
    cx.ensure_owned(cx.intake_path)
    with dataset_writable(cx.pile_dataset):
        cx.ensure_owned(cx.pile_path)
    with dataset_writable(cx.collection_dataset):
        cx.ensure_owned(cx.collection_path)


#####################
# static file stuff #
#####################


#####################
# replication stuff #
#####################


class ReplicationStatus(Enum):
    OK = "OK"
    EMPTY = "EMPTY"
    BEHIND = "BEHIND"
    DIVERGED = "DIVERGED"
    UNKNOWN = "UNKNOWN"


def replicate(src, dst):
    plan = build_replication_plan(src, dst)
    return execute_replication_plan(plan)


def replication_status(src, dst):
    src_guid = zfs.get_latest_guid(src)
    dst_guid = zfs.get_latest_guid(dst)

    if not dst_guid:
        return ReplicationStatus.EMPTY, "no snapshots on target"

    mapping = DatasetMapping(src, dst)

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


#####################
#   restore stuff   #
#####################


def restore_dataset(src_snap, dst, recursive=False, require_new=True):
    require_snapshot(src_snap)

    if require_new:
        require_new_dataset(dst)

    zfs.send_recv(src_snap, dst, recursive=recursive)

    snap_name = src_snap.split("@", 1)[1]
    if not zfs.snapshot_exists(f"{dst}@{snap_name}"):
        fatal("restore completed but snapshot missing at destination")


def restore_from_snapshot(src, dst, snap, recursive):
    src_snap = f"{src}@{snap}"
    restore_dataset(src_snap, dst, recursive=recursive)


def recover_dataset_tree(cx, target, replica, require_new=True):
    plan = build_recovery_plan(cx, target)
    execute_recovery_plan(plan)
    # normalise dataset properties
    apply_dataset_contract(cx)
    # ensure datasets are mountable and mounted
    zfs.mount()
    # Optional: runtime + ownership (debatable)
    #ensure_runtime_dirs(cx)
    #apply_ownership(cx)


@dataclass(frozen=True)
class RecoveryPlan:
    target: str
    replica: str
    snapshot: str
    recursive: bool


def build_recovery_plan(cx, target):
    mapping = DatasetMapping(cx.root_dataset, cx.replica_dataset)

    mapping.validate_within_src(target)
    require_within_dataset(target, cx.root_dataset)

    replica = mapping.map(target)
    require_dataset(replica)

    snap = zfs.latest_snapshot(replica)
    if not snap:
        fatal("no snapshots on replica")

    require_snapshot_of_dataset(snap, replica)

    require_new_dataset(target)

    return RecoveryPlan(
        target=target,
        replica=replica,
        snapshot=snap,
        recursive=True,
    )


def execute_recovery_plan(plan: RecoveryPlan, cx):
    restore_dataset(
        plan.snapshot,
        plan.target,
        recursive=plan.recursive,
    )
    normalize_system(cx)


@dataclass(frozen=True)
class RestorePlan:
    src_snapshot: str
    dst: str
    recursive: bool


def build_restore_plan(src, dst, snap, recursive):
    if "@" in snap:
        fatal("snapshot must not include dataset")
    src_snap = f"{src}@{snap}"
    require_snapshot(src_snap)
    require_snapshot_of_dataset(src_snap, src)
    require_new_dataset(dst)
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


def normalize_system(cx):
    apply_dataset_contract(cx)
    zfs.mount()
    ensure_runtime_dirs(cx)
    apply_ownership(cx)


@dataclass(frozen=True)
class ReplicationPlan:
    src: str
    dst: str
    snapshot: str
    base: str | None
    mode: str  # "full" | "incremental" | "noop"


def build_replication_plan(src, dst):
    last_src = zfs.latest_snapshot(src)
    last_dst = zfs.latest_snapshot(dst)

    if not last_src:
        fatal("no source snapshot")

    # if strict (need to change test mocks)
    require_dataset(src)
    if not last_dst:
        return ReplicationPlan( src, dst, last_src, None, "full")

    base = find_incremental_base(src, dst)

    if not base:
        fatal(f"base snapshot missing on source: {base}")

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


@dataclass(frozen=True)
class SnapshotPolicy:
    prefix: str
    hold: bool = False
    raw: bool = False

    def build_name(self, ts: str) -> str:
        if self.raw:
            return self.prefix
        return f"{self.prefix}-{ts}"


def create_snapshot_with_policy(policy: SnapshotPolicy, dataset: str, ts=None):
    if not dataset:
        fatal("dataset required for snapshot")

    ts = ts or snapshot_timestamp()
    name = policy.build_name(ts)

    zfs.snapshot(name, dataset)
    snap = f"{dataset}@{name}"

    if policy.hold:
        zfs.hold("repl-anchor", snap)

    return snap


def create_prefixed_snapshot(prefix, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]
    policy = SnapshotPolicy(prefix=prefix)
    return create_snapshot_with_policy(policy, dataset)


def create_anchor(anchor_type, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]
    if anchor_type == "daily":
        policy = SnapshotPolicy(prefix="daily", hold=False)
    elif anchor_type == "rotation":
        policy = SnapshotPolicy(prefix="rotation", hold=True)
    else:
        fatal("invalid anchor type")
    return create_snapshot_with_policy(policy, dataset)


def create_snapshot(name, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]
    policy = SnapshotPolicy(prefix=name, raw=True)
    return create_snapshot_with_policy(policy, dataset, ts="")


def validate_relative_path(path: Path):
    require_relative_path(path)


@dataclass(frozen=True)
class IngestOp:
    src: Path
    dst: Path
    dataset: str
    action: str


def build_ingest_ops(cx, files):
    ops = []
    for src in files:
        rel = src.relative_to(cx.intake_path)
        dst = cx.pile_path / "in" / rel
        require_no_conflict(src, dst)
        if dst.exists():
            action = 'noop'
        else:
            action = 'move'
        ops.append(IngestOp(
            src=src,
            dst=dst,
            dataset=cx.pile_dataset,
            action=action
        ))
    return ops


def execute_ingest_ops(cx, ops):
    muts = ingest_plan_mutations(ops)
    execute_semantic_mutations(cx, muts)


def ingest_plan_mutations(ops):
    muts = []
    for op in ops:
        if op.action == "move":
            muts.append(
                SemanticMutation(
                    action="move",
                    src=op.src,
                    dst=op.dst,
                    dataset=op.dataset,
                )
            )
        elif op.action == "noop":
            muts.append(
                SemanticMutation(
                    action="unlink",
                    src=op.src,
                    dst=None,
                    dataset=op.dataset,
                )
            )
    return muts


@dataclass(frozen=True)
class PromoteOp:
    action: str
    src: Path
    dst: Path | None
    dataset: str


@dataclass(frozen=True)
class PromotePlan:
    ops: list[PromoteOp]


def build_promote_plan(cx):
    out_path = cx.pile_path / "out"

    ops = []

    if not out_path.is_dir():
        return None

    # validate top-level dirs
    for child in out_path.iterdir():
        if child.name not in ("collection", "filing"):
            fatal(f"invalid /out/ structure: {child.name}")

    # collect files

    col_dir = out_path / "collection"
    fil_dir = out_path / "filing"
    col_files = sorted(iter_files(col_dir)) if col_dir.is_dir() else []
    fil_files = sorted(iter_files(fil_dir)) if fil_dir.is_dir() else []
    if not col_files and not fil_files:
        fatal("/out/ directory empty")

    # validate files

    def validate_file(cx, src: Path, rel: Path):
        r = cx.resolve(rel)
        require_dataset(r.dataset)
        require_no_conflict(src, r.path)

    for f in col_files:
        rel = Path("collection") / f.relative_to(col_dir)
        validate_file(cx, f, rel)
        r = cx.resolve(rel)
        if not r.path.is_file():
            op = PromoteOp(action="copy",
                           src=f,
                           dst=r.path,
                           dataset=r.dataset)
            ops.append(op)
        op = PromoteOp(action="unlink",
                       src=f,
                       dst=None,
                       dataset=cx.pile_dataset)
        ops.append(op)

    for f in fil_files:
        rel = f.relative_to(fil_dir)
        if len(rel.parts) < 2:
            fatal("invalid filing structure")
        subset = rel.parts[0]
        subpath = Path(*rel.parts[1:])
        full_rel = Path("filing") / subset / subpath
        validate_file(cx, f, full_rel)
        r = cx.resolve(full_rel)
        if not r.path.is_file():
            op = PromoteOp(action="copy",
                           src=f,
                           dst=r.path,
                           dataset=r.dataset)
            ops.append(op)
        op = PromoteOp(action="unlink",
                       src=f,
                       dst=None,
                       dataset=cx.pile_dataset)
        ops.append(op)

    return RewritePlan(ops=ops)


def execute_promote_plan(cx, plan):
    muts = promote_plan_mutations(plan.ops)
    execute_semantic_mutations(cx, muts)


def promote_plan_mutations(ops):
    def build(op):
        return SemanticMutation(action=op.action,
                                src=op.src,
                                dst=op.dst,
                                dataset=op.dataset)
    return [build(op) for op in ops]


@dataclass(frozen=True)
class ReplaceOp:
    src: Path
    dst: Resolved


@dataclass(frozen=True)
class ReplacePlan:
    ops: list[ReplaceOp]


def build_replace_plan(cx, src, dst_rel):
    require_file(src)
    resolved = cx.resolve(dst_rel)
    require_file(resolved.path)
    require_dataset(resolved.dataset)
    op = ReplaceOp(src=src, dst=resolved)
    return ReplacePlan(ops=[op])


def execute_replace_plan(cx, plan):
    muts = replace_plan_mutations(plan)
    execute_semantic_mutations(cx, muts)


def replace_plan_mutations(plan):
    def build(op):
        return SemanticMutation(action="copy",
                                src=op.src,
                                dst=op.dst.path,
                                dataset=op.dst.dataset)
    return [build(op) for op in plan.ops]


@dataclass(frozen=True)
class PruneOp:
    path: Path
    dataset: str


@dataclass(frozen=True)
class PrunePlan:
    ops: list[PruneOp]


def build_prune_plan(root, dataset):
    keep = (
        root / "in",
        root / "out",
        root / "sort",
    )

    ops = []
    would_remove = set()

    def would_be_empty(path):
        for x in path.iterdir():
            if x not in would_remove:
                return False
        return True

    for path in sorted(root.rglob("*"), reverse=True):
        if path in keep:
            continue

        if path.is_dir() and would_be_empty(path):
            would_remove.add(path)
            op = PruneOp(path=path, dataset=dataset)
            ops.append(op)

    return PrunePlan(ops=ops)


def prune_mutations(plan):
    def build(op):
        return SemanticMutation(action="rmdir",
                                src=op.path,
                                dst=None,
                                dataset=op.dataset)
    return [build(op) for op in plan.ops]


def execute_prune_plan(cx, ops):
    mut = prune_mutations(ops)
    execute_semantic_mutations(cx, mut)