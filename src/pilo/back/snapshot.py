from dataclasses import dataclass
import os

from .. import zfs
from ..error import fatal
from ..util import snapshot_timestamp


@dataclass(frozen=True)
class SnapshotPolicy:
    prefix: str
    hold: bool = False
    raw: bool = False

    def build_name(self, ts: str) -> str:
        if self.raw:
            return self.prefix
        return f"{self.prefix}-{ts}"


def create_snapshot_with_policy(policy: SnapshotPolicy, dataset: str, ts=None):
    if not dataset:
        fatal("dataset required for snapshot")

    ts = ts or snapshot_timestamp()
    name = policy.build_name(ts)

    zfs.snapshot(name, dataset)
    snap = f"{dataset}@{name}"

    if policy.hold:
        zfs.hold("repl-anchor", snap)

    return snap


def create_prefixed_snapshot(prefix, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]
    policy = SnapshotPolicy(prefix=prefix)
    return create_snapshot_with_policy(policy, dataset)


def create_anchor(anchor_type, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]
    if anchor_type == "daily":
        policy = SnapshotPolicy(prefix="daily", hold=False)
    elif anchor_type == "rotation":
        policy = SnapshotPolicy(prefix="rotation", hold=True)
    else:
        fatal("invalid anchor type")
    return create_snapshot_with_policy(policy, dataset)


def create_snapshot(name, dataset=None):
    dataset = dataset or os.environ["PILO_ROOT"]
    policy = SnapshotPolicy(prefix=name, raw=True)
    return create_snapshot_with_policy(policy, dataset, ts="")


