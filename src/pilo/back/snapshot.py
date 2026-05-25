from dataclasses import dataclass
from enum import Enum
import os

from .. import error
from .. import util
from .. import zfs


class SnapshotKind(Enum):
    MARK = "mark"
    REG = "reg"
    EXTRA = "extra"


@dataclass(frozen=True)
class SnapshotName:
    timestamp: str
    kind: SnapshotKind
    label: str | None = None

    def format(self) -> str:
        base = f"{self.timestamp}-{self.kind.value}"
        if self.label is not None:
            base += f"-{self.label}"
        return base


def parse_snapshot_name(name: str) -> SnapshotName | None:
    parts = name.split("-", 2)
    if len(parts) < 2:
        return None
    ts, kind_str = parts[0], parts[1]
    try:
        kind = SnapshotKind(kind_str)
    except ValueError:
        return None
    label = parts[2] if len(parts) > 2 else None
    if kind is SnapshotKind.EXTRA and label is None:
        return None
    if kind is not SnapshotKind.EXTRA and label is not None:
        return None
    return SnapshotName(timestamp=ts, kind=kind, label=label)


def classify_snapshot(name: str) -> SnapshotKind | None:
    parsed = parse_snapshot_name(name)
    return parsed.kind if parsed is not None else None


def is_mark_snapshot(name: str) -> bool:
    return classify_snapshot(name) is SnapshotKind.MARK


def is_reg_snapshot(name: str) -> bool:
    return classify_snapshot(name) is SnapshotKind.REG


def is_extra_snapshot(name: str) -> bool:
    return classify_snapshot(name) is SnapshotKind.EXTRA


def _create_canonical_snapshot(kind: SnapshotKind, dataset: str,
                                ts: str | None = None, label: str | None = None):
    if not dataset:
        error.fatal("dataset required for snapshot")
    ts = ts or util.snapshot_timestamp()
    name = SnapshotName(timestamp=ts, kind=kind, label=label).format()
    zfs.snapshot(name, dataset)
    return f"{dataset}@{name}"


def create_mark_snapshot(dataset: str, ts: str | None = None) -> str:
    return _create_canonical_snapshot(SnapshotKind.MARK, dataset, ts=ts)


def create_reg_snapshot(dataset: str, ts: str | None = None) -> str:
    return _create_canonical_snapshot(SnapshotKind.REG, dataset, ts=ts)


def create_extra_snapshot(dataset: str, label: str,
                          ts: str | None = None) -> str:
    return _create_canonical_snapshot(SnapshotKind.EXTRA, dataset,
                                      ts=ts, label=label)


@dataclass(frozen=True)
class SnapshotPolicy:
    prefix: str
    raw: bool = False

    def build_name(self, ts: str) -> str:
        if self.raw:
            return self.prefix
        return f"{self.prefix}-{ts}"


def create_snapshot_with_policy(policy: SnapshotPolicy, dataset: str, ts=None):
    if not dataset:
        error.fatal("dataset required for snapshot")

    ts = ts or util.snapshot_timestamp()
    name = policy.build_name(ts)

    zfs.snapshot(name, dataset)
    snap = f"{dataset}@{name}"

    return snap


def create_prefixed_snapshot(prefix, dataset=None):
    dataset = dataset or os.environ["PILO_PRIMARY_ROOT"]
    policy = SnapshotPolicy(prefix=prefix)
    return create_snapshot_with_policy(policy, dataset)


def create_snapshot(name, dataset=None):
    dataset = dataset or os.environ["PILO_PRIMARY_ROOT"]
    policy = SnapshotPolicy(prefix=name, raw=True)
    return create_snapshot_with_policy(policy, dataset, ts="")
