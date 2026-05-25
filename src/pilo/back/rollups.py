from dataclasses import dataclass
from pathlib import Path

from .snapshot import is_mark_snapshot
from .stream_gc import oldest_held_timestamp
from .streams import (
    stream_output_path,
    verify_one,
    write_rollup_manifest,
)
from .. import zfs


@dataclass(frozen=True)
class RollupOp:
    output_path: Path
    base_snapshot: str
    target_snapshot: str
    source_dataset: str


@dataclass(frozen=True)
class RollupPlan:
    ops: tuple[RollupOp, ...]


def rollup_filename(base_name: str, target_name: str) -> str:
    base_ts = base_name.split("-")[0]
    target_ts = target_name.split("-")[0]
    return f"{base_ts}--{target_ts}.rollup.zfs"


def rollup_output_path(target_name: str, filename: str) -> Path:
    target_ts = target_name.split("-")[0]
    return stream_output_path() / target_ts[:8] / filename


def discover_rollup_chain(dataset):
    cutoff_ts = oldest_held_timestamp(dataset)
    if cutoff_ts is None:
        return []
    marks = []
    for full_ref, _ in zfs.snapshots_userrefs(dataset):
        name = full_ref.split("@", 1)[1]
        if is_mark_snapshot(name):
            ts = name.split("-")[0]
            if ts >= cutoff_ts:
                marks.append(name)
    return [(marks[i], marks[i + 1])
            for i in range(len(marks) - 1)]


def build_rollup_plan(dataset) -> RollupPlan:
    pairs = discover_rollup_chain(dataset)
    ops = []
    for base_name, target_name in pairs:
        fname = rollup_filename(base_name, target_name)
        out_path = rollup_output_path(target_name, fname)
        if out_path.exists():
            status, _ = verify_one(out_path)
            if status == "OK":
                continue
        base_ref = f"{dataset}@{base_name}"
        target_ref = f"{dataset}@{target_name}"
        ops.append(RollupOp(
            output_path=out_path,
            base_snapshot=base_ref,
            target_snapshot=target_ref,
            source_dataset=dataset,
        ))
    return RollupPlan(ops=tuple(ops))


def execute_rollup_plan(plan: RollupPlan):
    for op in plan.ops:
        zfs.send_incremental_to_file(
            op.base_snapshot, op.target_snapshot, op.output_path,
        )
        guid = zfs.get_guid(op.target_snapshot)
        target_name = op.target_snapshot.split("@", 1)[1]
        base_name = op.base_snapshot.split("@", 1)[1]
        write_rollup_manifest(
            op.output_path,
            snapshot_name=target_name,
            source=op.source_dataset,
            guid=guid,
            base_snapshot=base_name,
        )
        yield op.output_path
