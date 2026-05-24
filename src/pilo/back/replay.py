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
    snapshot: str
    source: str
    target_dataset: str
    applied_at: str


def find_streams(path):
    path = Path(path)
    streams = sorted(path.glob(f"*{STREAM_SUFFIX}"))
    return [s for s in streams if not str(s).endswith(MANIFEST_SUFFIX)]


def build_batch_replay_plan(paths, target_dataset=None):
    plans = []
    for p in paths:
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
        snapshot=plan.manifest.snapshot,
        source=plan.manifest.source,
        target_dataset=plan.target_dataset,
        applied_at=datetime.now(timezone.utc).isoformat(),
    )
