from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SemanticMutation:
    action: str
    src: Path | None
    dst: Path | None
    dataset: str


@dataclass(frozen=True)
class MoveMutation:
    src: Path
    dst: Path
    dataset: str


@dataclass(frozen=True)
class CopyMutation:
    src: Path
    dst: Path
    dataset: str


@dataclass(frozen=True)
class UnlinkMutation:
    path: Path
    dataset: str


@dataclass(frozen=True)
class RmdirMutation:
    path: Path
    dataset: str
