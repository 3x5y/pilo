from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from . import error
from . import validation


def domain(rel: Path):
    parts = rel.parts
    if not parts:
        return "invalid"

    if parts[0] in ("in", "out", "sort"):
        return "pile"
    if parts[0] in ("collection", "filing"):
        return "static"
    return "invalid"


class StorageDomain(Enum):
    PILE = "pile"
    COLLECTION = "collection"
    FILING = "filing"


@dataclass(frozen=True)
class LogicalPath:
    domain: StorageDomain
    relpath: Path


@dataclass(frozen=True)
class ResolvedPath:
    logical: LogicalPath
    physical: Path
    dataset: str
    @property
    def path(self):
        return self.physical


@dataclass
class Resolved:
    path: Path
    dataset: str


def parse_logical_path(path: Path) -> LogicalPath:
    if not path.parts:
        error.fatal("empty path")

    validation.require_relative_path(path)

    top = path.parts[0]

    if top in ("in", "out", "sort"):
        return LogicalPath(
            domain=StorageDomain.PILE,
            relpath=path,
        )

    if top == "collection":
        if len(path.parts) < 2:
            error.fatal("invalid collection path")

        return LogicalPath(
            domain=StorageDomain.COLLECTION,
            relpath=Path(*path.parts[1:]),
        )

    if top == "filing":
        if len(path.parts) < 3:
            error.fatal("invalid filing path")

        return LogicalPath(
            domain=StorageDomain.FILING,
            relpath=Path(*path.parts[1:]),
        )

    error.fatal(f"invalid path: {path}")
