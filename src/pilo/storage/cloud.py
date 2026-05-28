import json
import os
from dataclasses import dataclass
from pathlib import Path


STREAM_SUFFIX = ".zfs"
MANIFEST_SUFFIX = ".zfs.manifest"


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
