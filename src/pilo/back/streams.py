import os
from pathlib import Path

from .snapshot import SnapshotName
from .. import zfs

STREAM_SUFFIX = ".zfs"


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


def export_incremental_stream(dataset: str, snapshot: SnapshotName,
                              base: SnapshotName | None = None) -> Path:
    filepath = stream_filepath(snapshot)
    snap = f"{dataset}@{snapshot.format()}"
    if base is not None:
        base_snap = f"{dataset}@{base.format()}"
        zfs.send_incremental_to_file(base_snap, snap, filepath)
    else:
        zfs.send_full_to_file(snap, filepath)
    return filepath
