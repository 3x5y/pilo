from dataclasses import dataclass
import os

from .. import error
from .. import util
from .. import zfs


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
