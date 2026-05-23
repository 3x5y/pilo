import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .snapshot import SnapshotName
from .. import fs
from .. import zfs

STREAM_SUFFIX = ".zfs"
MANIFEST_SUFFIX = ".zfs.manifest"


@dataclass(frozen=True)
class StreamManifest:
    stream: str
    snapshot: str
    source: str
    guid: str
    checksum: str
    size: int
    created: str

    def to_dict(self) -> dict:
        return {
            "stream": self.stream,
            "snapshot": self.snapshot,
            "source": self.source,
            "guid": self.guid,
            "checksum": self.checksum,
            "size": self.size,
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StreamManifest":
        try:
            size = d["size"]
            if not isinstance(size, int):
                raise ValueError("size must be int")
            return cls(
                stream=d["stream"],
                snapshot=d["snapshot"],
                source=d["source"],
                guid=d["guid"],
                checksum=d["checksum"],
                size=size,
                created=d["created"],
            )
        except KeyError as e:
            raise ValueError(f"missing field: {e}") from e


def stream_output_path() -> Path:
    return Path(os.environ["PILO_STREAM_OUTPUT_PATH"])


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
    )
    manifest_path = stream_path.with_suffix(MANIFEST_SUFFIX)
    manifest_path.write_text(json.dumps(entry.to_dict(), indent=2) + "\n")
    return manifest_path


def load_stream_manifest(path: Path) -> StreamManifest:
    data = json.loads(path.read_text())
    return StreamManifest.from_dict(data)


def export_incremental_stream(dataset: str, snapshot: SnapshotName,
                              base: SnapshotName | None = None) -> Path:
    filepath = stream_filepath(snapshot)
    snap = f"{dataset}@{snapshot.format()}"
    if base is not None:
        base_snap = f"{dataset}@{base.format()}"
        zfs.send_incremental_to_file(base_snap, snap, filepath)
    else:
        zfs.send_full_to_file(snap, filepath)
    guid = zfs.get_guid(snap)
    write_stream_manifest(filepath, snapshot.format(), dataset, guid)
    return filepath
