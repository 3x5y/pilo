from dataclasses import dataclass
from pathlib import Path
import shutil

from .snapshot import is_mark_snapshot
from .streams import MANIFEST_SUFFIX
from .. import error
from .. import zfs


@dataclass(frozen=True)
class StreamGcOp:
    stream_path: Path
    manifest_path: Path | None


@dataclass(frozen=True)
class StreamGcPlan:
    ops: tuple[StreamGcOp, ...]


def oldest_held_timestamp(dataset):
    for full_ref, refs in zfs.snapshots_userrefs(dataset):
        if refs > 0:
            name = full_ref.split("@", 1)[1]
            if is_mark_snapshot(name):
                return name.split("-")[0]
    return None


def _effective_ts(path: Path) -> str | None:
    name = path.name
    if "--" in name:
        parts = name.split("--", 1)
        if len(parts) > 1:
            return parts[1].split(".")[0]
        return None
    return name.split("-", 1)[0]


def _find_streams(path: Path) -> list[Path]:
    return sorted(Path(path).rglob("*.zfs"))


def build_gc_plan(dataset, output_path, keep=0):
    cutoff_ts = oldest_held_timestamp(dataset)
    if cutoff_ts is None:
        return StreamGcPlan(ops=())

    all_streams = _find_streams(output_path)

    candidates = []
    for p in all_streams:
        ts = _effective_ts(p)
        if ts and ts < cutoff_ts:
            candidates.append((ts, p))

    candidates.sort(key=lambda x: x[0], reverse=True)

    to_prune = candidates[keep:]

    rels = [p.relative_to(output_path) for _, p in to_prune]
    if len(rels) != len(set(rels)):
        error.fatal("stream-gc: duplicate relative paths in prune set")

    ops = []
    for _, stream_path in to_prune:
        manifest_path = stream_path.with_suffix(MANIFEST_SUFFIX)
        ops.append(StreamGcOp(
            stream_path=stream_path,
            manifest_path=manifest_path if manifest_path.exists() else None,
        ))

    return StreamGcPlan(ops=tuple(ops))


def execute_gc_plan(plan, output_path, gc_path=None):
    for op in plan.ops:
        if gc_path:
            rel = op.stream_path.relative_to(output_path)
            dst = Path(gc_path) / rel
            if dst.exists():
                error.fatal(
                    f"stream-gc: destination already exists: {dst}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(op.stream_path), str(dst))
            if op.manifest_path:
                rel_m = op.manifest_path.relative_to(output_path)
                dst_m = Path(gc_path) / rel_m
                if not dst_m.exists():
                    dst_m.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(op.manifest_path), str(dst_m))
        else:
            op.stream_path.unlink()
            if op.manifest_path and op.manifest_path.exists():
                op.manifest_path.unlink()
        yield op.stream_path
