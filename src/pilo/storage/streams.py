import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .snapshot import SnapshotName
from .. import error
from .. import fs
from .. import zfs

STREAM_SUFFIX = ".zfs"
MANIFEST_SUFFIX = ".zfs.manifest"

KIND_FULL = "full"
KIND_INCREMENTAL = "incremental"
KIND_ROLLUP = "rollup"

_VALID_KINDS = {KIND_FULL, KIND_INCREMENTAL, KIND_ROLLUP}


@dataclass(frozen=True)
class StreamManifest:
    stream: str
    snapshot: str
    source: str
    guid: str
    checksum: str
    size: int
    created: str
    kind: str = KIND_INCREMENTAL
    base_snapshot: str | None = None

    def to_dict(self) -> dict:
        return {
            "stream": self.stream,
            "snapshot": self.snapshot,
            "source": self.source,
            "guid": self.guid,
            "checksum": self.checksum,
            "size": self.size,
            "created": self.created,
            "kind": self.kind,
            "base_snapshot": self.base_snapshot,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StreamManifest":
        try:
            size = d["size"]
            if not isinstance(size, int):
                raise ValueError("size must be int")
            kind = d.get("kind", KIND_INCREMENTAL)
            if kind not in _VALID_KINDS:
                raise ValueError(f"invalid stream kind: {kind}")
            return cls(
                stream=d["stream"],
                snapshot=d["snapshot"],
                source=d["source"],
                guid=d["guid"],
                checksum=d["checksum"],
                size=size,
                created=d["created"],
                kind=kind,
                base_snapshot=d.get("base_snapshot"),
            )
        except KeyError as e:
            raise ValueError(f"missing field: {e}") from e


def stream_output_path() -> Path:
    path = os.environ.get("PILO_STREAM_OUTPUT_PATH")
    if not path:
        error.fatal("PILO_STREAM_OUTPUT_PATH is not set")
    return Path(path)


def stream_filename(ts: str, kind: str) -> str:
    return f"{ts}-{kind}{STREAM_SUFFIX}"


def stream_date_dir(ts: str) -> str:
    return ts[:8]


def stream_filepath(snapshot: SnapshotName) -> Path:
    return (
        stream_output_path()
        / stream_date_dir(snapshot.timestamp)
        / stream_filename(snapshot.timestamp, snapshot.kind.value)
    )


def manifest_filename(snapshot: SnapshotName) -> str:
    return f"{snapshot.timestamp}-{snapshot.kind.value}{MANIFEST_SUFFIX}"


def manifest_filepath(snapshot: SnapshotName) -> Path:
    return (
        stream_output_path()
        / stream_date_dir(snapshot.timestamp)
        / manifest_filename(snapshot)
    )


def write_stream_manifest(
    stream_path: Path,
    snapshot_name: str,
    source: str,
    guid: str,
    kind: str = KIND_INCREMENTAL,
    base_snapshot: str | None = None,
) -> Path:
    checksum = fs.sha256_file(stream_path)
    size = stream_path.stat().st_size
    entry = StreamManifest(
        stream=str(stream_path.relative_to(stream_output_path())),
        snapshot=snapshot_name,
        source=source,
        guid=guid,
        checksum=checksum,
        size=size,
        created=datetime.now(timezone.utc).isoformat(),
        kind=kind,
        base_snapshot=base_snapshot,
    )
    manifest_path = stream_path.with_suffix(MANIFEST_SUFFIX)
    manifest_path.write_text(json.dumps(entry.to_dict(), indent=2) + "\n")
    return manifest_path


def write_incremental_manifest(
    stream_path: Path,
    snapshot_name: str,
    source: str,
    guid: str,
    base_snapshot: str | None = None,
) -> Path:
    return write_stream_manifest(
        stream_path, snapshot_name, source, guid,
        kind=KIND_INCREMENTAL, base_snapshot=base_snapshot,
    )


def write_rollup_manifest(
    stream_path: Path,
    snapshot_name: str,
    source: str,
    guid: str,
    base_snapshot: str,
) -> Path:
    return write_stream_manifest(
        stream_path, snapshot_name, source, guid,
        kind=KIND_ROLLUP, base_snapshot=base_snapshot,
    )


def load_stream_manifest(path: Path) -> StreamManifest:
    data = json.loads(path.read_text())
    return StreamManifest.from_dict(data)


def verify_one(path: Path):
    if not path.exists():
        return ("NOT_FOUND", str(path))

    if str(path).endswith(MANIFEST_SUFFIX):
        stream_path = path.with_suffix("")
        if not stream_path.exists():
            return ("NOT_FOUND", str(stream_path))
        try:
            manifest = load_stream_manifest(path)
            actual = fs.sha256_file(stream_path)
            if actual == manifest.checksum:
                return ("OK", str(path))
            else:
                return ("MISMATCH", str(path))
        except Exception as e:
            return ("ERROR", f"{path}: {e}")

    if path.suffix == ".zfs":
        manifest_path = path.with_suffix(MANIFEST_SUFFIX)
        if not manifest_path.exists():
            return ("NO_MANIFEST", str(path))
        try:
            manifest = load_stream_manifest(manifest_path)
            actual = fs.sha256_file(path)
            if actual == manifest.checksum:
                return ("OK", str(path))
            else:
                return ("MISMATCH", str(path))
        except Exception as e:
            return ("ERROR", f"{path}: {e}")

    return ("NOT_STREAM", str(path))


def export_incremental_stream(dataset: str, snapshot: SnapshotName,
                              base: SnapshotName | None = None) -> Path:
    filepath = stream_filepath(snapshot)
    snap = f"{dataset}@{snapshot.format()}"
    if base is not None:
        base_snap = f"{dataset}@{base.format()}"
        zfs.send_incremental_to_file(base_snap, snap, filepath)
        kind = KIND_INCREMENTAL
        base_name = base.format()
    else:
        zfs.send_full_to_file(snap, filepath)
        kind = KIND_FULL
        base_name = None
    guid = zfs.get_guid(snap)
    write_stream_manifest(
        filepath, snapshot.format(), dataset, guid,
        kind=kind, base_snapshot=base_name,
    )
    return filepath
