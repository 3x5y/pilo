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

from .back.replication import *
from .back.snapshot import *

from .front.ingest import *
from .front.manifest_verify import *
from .front.promote import *
from .front.prune import *
from .front.replace import *
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


def validate_relative_path(path: Path):
    require_relative_path(path)