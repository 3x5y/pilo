from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from . import error


@dataclass(frozen=True)
class ManifestEntry:
    checksum: str
    path: Path


@dataclass(frozen=True)
class ManifestAddEntry:
    subset: str
    entry: ManifestEntry


@dataclass(frozen=True)
class ManifestRemoveEntry:
    subset: str
    path: Path


class ChecksumProvenance(Enum):
    MANIFEST = "manifest"
    VERIFIED = "verified"
    GENERATED = "generated"


@dataclass(frozen=True)
class ProvenancedChecksum:
    path: Path
    checksum: str
    provenance: ChecksumProvenance


class ManifestIndex:

    def __init__(self, entries):
        self._entries = {}
        for entry in entries:
            self._entries[entry.path] = entry

    def lookup(self, path: Path):
        return self._entries.get(path)

    def require(self, path: Path):
        entry = self.lookup(path)
        if entry is None:
            error.fatal(f"manifest entry missing: {path}")
        return entry


class ChecksumIndex:

    def __init__(self, checksums):
        self._checksums = {}
        for item in checksums:
            normalized = as_provenanced_checksum(item)
            self._checksums[normalized.path] = normalized

    def lookup(self, path: Path):
        return self._checksums.get(path)

    def require(self, path: Path):
        item = self.lookup(path)

        if item is None:
            error.fatal(
                f"verified checksum missing: {path}"
            )

        return item


# compat helpers

def as_manifest_index(entries):
    if isinstance(entries, ManifestIndex):
        return entries
    return ManifestIndex(entries)


def as_checksum_index(items):
    if isinstance(items, ChecksumIndex):
        return items
    if isinstance(items, dict):
        items = items.values()
    return ChecksumIndex(items)


def build_generated_checksum(path, checksum):
    return ProvenancedChecksum(
        path=path,
        checksum=checksum,
        provenance=(
            ChecksumProvenance.GENERATED
        ),
    )


def as_provenanced_checksum(item):

    if isinstance(item, ProvenancedChecksum):
        return item

    if isinstance(item, ManifestEntry):
        return ProvenancedChecksum(
            path=item.path,
            checksum=item.checksum,
            provenance=(
                ChecksumProvenance.MANIFEST
            ),
        )

    error.fatal(
        f"unsupported checksum item: "
        f"{type(item).__name__}"
    )
