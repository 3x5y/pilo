from dataclasses import dataclass
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



@dataclass(frozen=True)
class VerifiedChecksum:
    path: Path
    checksum: str


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


class VerifiedChecksumIndex:

    def __init__(self, checksums):
        self._checksums = {}

        for item in checksums:
            self._checksums[item.path] = item

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


def as_verified_checksum_index(items):
    if isinstance(items, VerifiedChecksumIndex):
        return items
    if isinstance(items, dict):
        items = items.values()
    return VerifiedChecksumIndex(items)
