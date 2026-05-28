import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from . import streams
from .. import fs


STREAM_SUFFIX = ".zfs"
MANIFEST_SUFFIX = ".zfs.manifest"

_VALID_STAMP_RE = re.compile(r"^\d{8}_\d{6}$")
_SAFE_FILENAME_RE = re.compile(r"^[a-zA-Z0-9_.-]+$")


@dataclass(frozen=True)
class PackageEntry:
    path: str
    checksum: str
    size: int

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "checksum": self.checksum,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PackageEntry":
        try:
            size = d["size"]
            if not isinstance(size, int):
                raise ValueError("size must be int")
            return cls(
                path=d["path"],
                checksum=d["checksum"],
                size=size,
            )
        except KeyError as e:
            raise ValueError(f"missing field: {e}") from e


@dataclass(frozen=True)
class PackageManifest:
    archive: str
    checksum: str
    size: int
    created: str
    entries: tuple[PackageEntry, ...]

    def to_dict(self) -> dict:
        return {
            "archive": self.archive,
            "checksum": self.checksum,
            "size": self.size,
            "created": self.created,
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PackageManifest":
        try:
            size = d["size"]
            if not isinstance(size, int):
                raise ValueError("size must be int")
            entries_raw = d["entries"]
            if not isinstance(entries_raw, list):
                raise ValueError("entries must be a list")
            entries = tuple(PackageEntry.from_dict(e) for e in entries_raw)
            _validate_package_entries(entries)
            return cls(
                archive=d["archive"],
                checksum=d["checksum"],
                size=size,
                created=d["created"],
                entries=entries,
            )
        except KeyError as e:
            raise ValueError(f"missing field: {e}") from e


@dataclass(frozen=True)
class CloudManifest:
    version: int
    format: str
    recipient: str
    checksum: str
    size: int
    package: PackageManifest
    created: str

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "format": self.format,
            "recipient": self.recipient,
            "checksum": self.checksum,
            "size": self.size,
            "package": self.package.to_dict(),
            "created": self.created,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CloudManifest":
        try:
            version = d["version"]
            if not isinstance(version, int):
                raise ValueError("version must be int")
            size = d["size"]
            if not isinstance(size, int):
                raise ValueError("size must be int")
            return cls(
                version=version,
                format=d["format"],
                recipient=d["recipient"],
                checksum=d["checksum"],
                size=size,
                package=PackageManifest.from_dict(d["package"]),
                created=d["created"],
            )
        except KeyError as e:
            raise ValueError(f"missing field: {e}") from e


def validate_pack_input(src_dir: Path, dst_dir: Path, stamp: str) -> None:
    if not src_dir.is_dir():
        raise ValueError(f"not a directory: {src_dir}")
    if not _VALID_STAMP_RE.match(stamp):
        raise ValueError(f"invalid stamp, expected YYYYMMDD_HHMMSS: {stamp}")
    if dst_dir.exists() and not dst_dir.is_dir():
        raise ValueError(f"output path exists and is not a directory: {dst_dir}")
    archive_path = dst_dir / f"{stamp}.tar.zst"
    if archive_path.exists():
        raise ValueError(f"output already exists: {archive_path}")
    manifest_path = dst_dir / f"{stamp}.tar.zst.manifest"
    if manifest_path.exists():
        raise ValueError(f"output already exists: {manifest_path}")

    for f in sorted(src_dir.iterdir()):
        if f.is_symlink():
            raise ValueError(f"symlink not allowed: {f.name}")
        if f.is_dir():
            raise ValueError(f"nested directory not allowed: {f.name}")
        if not f.is_file():
            raise ValueError(f"unexpected entry type: {f.name}")
        if f.name.startswith("."):
            raise ValueError(f"hidden file not allowed: {f.name}")
        if not _SAFE_FILENAME_RE.match(f.name):
            raise ValueError(f"malformed filename: {f.name}")
        if not (f.name.endswith(STREAM_SUFFIX) or f.name.endswith(MANIFEST_SUFFIX)):
            raise ValueError(f"unexpected file type: {f.name}")


def build_package_manifest(
    stamp: str,
    archive_checksum: str,
    archive_size: int,
    created: str,
    entries: tuple[PackageEntry, ...],
) -> CloudManifest:
    pkg = PackageManifest(
        archive=f"{stamp}.tar.zst",
        checksum=archive_checksum,
        size=archive_size,
        created=created,
        entries=entries,
    )
    return CloudManifest(
        version=1,
        format="tar.zst",
        recipient="",
        checksum=archive_checksum,
        size=archive_size,
        package=pkg,
        created=created,
    )


def pack_stream_day(src_dir: Path, dst_dir: Path) -> Path:
    now = datetime.now(timezone.utc)
    date_prefix = src_dir.name
    stamp = f"{date_prefix}_{now.strftime('%H%M%S')}"
    validate_pack_input(src_dir, dst_dir, stamp)
    dst_dir.mkdir(parents=True, exist_ok=True)

    manifest_files = sorted(src_dir.glob(f"*{MANIFEST_SUFFIX}"))
    if not manifest_files:
        raise ValueError("no stream manifests found")

    for mf in manifest_files:
        status, msg = streams.verify_one(mf)
        if status != "OK":
            raise ValueError(f"stream verification failed: {msg}")

    created = now.isoformat()

    with TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        tmp_archive = tmp_dir / f"{stamp}.tar.zst"

        subprocess.run(
            [
                "tar", "--zstd", "-cf", str(tmp_archive),
                "-C", str(src_dir.parent),
                "--sort=name",
                "--owner=0:0", "--group=0:0",
                "--mode=644",
                "--mtime=@0",
                date_prefix,
            ],
            check=True,
        )

        archive_checksum = fs.hash_file1(tmp_archive)
        archive_size = tmp_archive.stat().st_size

        entries = []
        for mf in manifest_files:
            rel = str(mf.relative_to(src_dir))
            entries.append(PackageEntry(
                path=rel,
                checksum=fs.hash_file1(mf),
                size=mf.stat().st_size,
            ))

        manifest = build_package_manifest(
            stamp=stamp,
            archive_checksum=archive_checksum,
            archive_size=archive_size,
            created=created,
            entries=tuple(entries),
        )
        tmp_manifest = tmp_dir / f"{stamp}.tar.zst.manifest"
        write_package_manifest(manifest, tmp_manifest)

        dst_archive = dst_dir / f"{stamp}.tar.zst"
        dst_manifest = dst_dir / f"{stamp}.tar.zst.manifest"
        shutil.move(str(tmp_archive), str(dst_archive))
        shutil.move(str(tmp_manifest), str(dst_manifest))

    return dst_archive


def _validate_package_entries(entries: tuple[PackageEntry, ...]) -> None:
    for entry in entries:
        p = entry.path
        if os.path.isabs(p):
            raise ValueError(f"absolute path not allowed: {p}")
        if p.endswith(STREAM_SUFFIX) and not p.endswith(MANIFEST_SUFFIX):
            raise ValueError(f".zfs stream path not allowed: {p}")


def write_package_manifest(manifest: CloudManifest, path: Path) -> None:
    text = json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"
    path.write_text(text)


def load_package_manifest(path: Path) -> CloudManifest:
    data = json.loads(path.read_text())
    return CloudManifest.from_dict(data)
