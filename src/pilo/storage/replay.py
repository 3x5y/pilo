from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .streams import (
    load_stream_manifest,
    verify_one,
    MANIFEST_SUFFIX,
    STREAM_SUFFIX,
)
from .. import error
from .. import zfs

ROLLUP_SUFFIXES = ("-rollup.zfs", ".rollup.zfs")


def is_rollup_stream(path: Path) -> bool:
    return str(path).endswith(ROLLUP_SUFFIXES)


def order_streams(paths: list[Path]) -> list[Path]:
    rollups = sorted(p for p in paths if is_rollup_stream(p))
    others = sorted(p for p in paths if not is_rollup_stream(p))
    return rollups + others


@dataclass(frozen=True)
class ReplayPlan:
    stream_path: Path
    manifest: object
    target_dataset: str


@dataclass(frozen=True)
class BatchReplayPlan:
    plans: tuple[ReplayPlan, ...]


@dataclass(frozen=True)
class ReplayResult:
    status: str
    stream: str
    snapshot: str
    source: str
    target_dataset: str
    applied_at: str


def find_streams(path):
    path = Path(path)
    streams = sorted(path.rglob(f"*{STREAM_SUFFIX}"))
    return [s for s in streams if not str(s).endswith(MANIFEST_SUFFIX)]


def build_batch_replay_plan(paths, target_dataset=None):
    ordered = order_streams(list(paths))
    plans = []
    for p in ordered:
        plans.append(build_replay_plan(p, target_dataset))
    return BatchReplayPlan(plans=tuple(plans))


def build_replay_plan(stream_path, target_dataset=None):
    stream_path = Path(stream_path)
    manifest_path = stream_path.with_suffix(MANIFEST_SUFFIX)
    if not manifest_path.exists():
        error.fatal(f"manifest not found: {manifest_path}")

    manifest = load_stream_manifest(manifest_path)

    status, _ = verify_one(stream_path)
    if status != "OK":
        error.fatal(f"stream verification failed: {status}")

    target = target_dataset or manifest.source

    return ReplayPlan(
        stream_path=stream_path,
        manifest=manifest,
        target_dataset=target,
    )


def execute_batch_replay_plan(batch_plan):
    for plan in batch_plan.plans:
        yield execute_replay_plan(plan)


def execute_replay_plan(plan):
    snap_ref = f"{plan.target_dataset}@{plan.manifest.snapshot}"
    if zfs.snapshot_exists(snap_ref):
        existing_guid = zfs.get_guid(snap_ref)
        if existing_guid == plan.manifest.guid:
            return ReplayResult(
                status="SKIPPED",
                stream=plan.manifest.stream,
                snapshot=plan.manifest.snapshot,
                source=plan.manifest.source,
                target_dataset=plan.target_dataset,
                applied_at=datetime.now(timezone.utc).isoformat(),
            )
        error.fatal(
            f"snapshot {plan.manifest.snapshot} exists on "
            f"{plan.target_dataset} but GUID mismatch: "
            f"expected {plan.manifest.guid}, got {existing_guid}")

    zfs.recv_file(plan.stream_path, plan.target_dataset)
    return ReplayResult(
        status="APPLIED",
        stream=plan.manifest.stream,
        snapshot=plan.manifest.snapshot,
        source=plan.manifest.source,
        target_dataset=plan.target_dataset,
        applied_at=datetime.now(timezone.utc).isoformat(),
    )


def filter_newer_than(paths: list[Path], snapshot_name: str) -> list[Path]:
    from . import snapshot as snapmod
    baseline_key = snapmod.snapshot_sort_key(snapshot_name)
    result = []
    for p in paths:
        manifest_path = Path(p).with_suffix(MANIFEST_SUFFIX)
        if not manifest_path.exists():
            error.fatal(f"manifest not found: {manifest_path}")
        manifest = load_stream_manifest(manifest_path)
        stream_key = snapmod.snapshot_sort_key(manifest.snapshot)
        if stream_key > baseline_key:
            result.append(p)
    return result
