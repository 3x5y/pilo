from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class PathParseError(ValueError):
    pass


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


def validate_relative_path(path: Path):
    if path.is_absolute():
        raise PathParseError("absolute paths not allowed")

    if ".." in path.parts:
        raise PathParseError("parent traversal not allowed")


def parse_logical_path(path: Path) -> LogicalPath:
    from . import error
    try:
        return try_parse_logical_path(path)
    except PathParseError as e:
        error.fatal(str(e))


def try_parse_logical_path(path: Path) -> LogicalPath:
    if not path.parts:
        raise PathParseError("empty path")

    validate_relative_path(path)

    top = path.parts[0]

    if top in ("in", "out", "sort"):
        return LogicalPath(
            domain=StorageDomain.PILE,
            relpath=path,
        )

    if top == "collection":
        if len(path.parts) < 2:
            raise PathParseError("invalid collection path")

        return LogicalPath(
            domain=StorageDomain.COLLECTION,
            relpath=Path(*path.parts[1:]),
        )

    if top == "filing":
        if len(path.parts) < 3:
            raise PathParseError("invalid filing path")

        return LogicalPath(
            domain=StorageDomain.FILING,
            relpath=Path(*path.parts[1:]),
        )

    raise PathParseError(f"invalid path: {path}")
