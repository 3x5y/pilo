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
