from dataclasses import dataclass

from .. import error
from .. import zfs


@dataclass(frozen=True)
class ContinuityAnchor:
    secondary_label: str
    snapshot: str


def hold_tag(label: str) -> str:
    return f"pilo:{label}"


def anchors(cx, label=None):
    result = []
    for config in cx.secondary_configs:
        if label is not None and config.label != label:
            continue
        tag = hold_tag(config.label)
        for snap in zfs.held_snapshots(cx.root_dataset, tag=tag):
            result.append(
                ContinuityAnchor(
                    secondary_label=config.label,
                    snapshot=snap,
                )
            )
    return result


def latest_anchor(cx, label):
    held = anchors(cx, label=label)
    if not held:
        return None
    return held[-1]


def apply_hold(cx, label, snapshot):
    tag = hold_tag(label)
    zfs.hold(tag, snapshot)


def release_hold(cx, label, snapshot):
    tag = hold_tag(label)
    zfs.release(tag, snapshot)


def label_for_secondary(cx, root_dataset):
    for config in cx.secondary_configs:
        if config.root == root_dataset:
            return config.label
    error.fatal(f"no secondary config found for {root_dataset}")


def resolve_label(cx, root_dataset):
    label = label_for_secondary(cx, root_dataset)
    tag = hold_tag(label)
    snaps = zfs.held_snapshots(root_dataset, tag=tag)
    if not snaps:
        error.fatal(
            f"no snapshot on {root_dataset} with hold {tag}"
        )
    return ContinuityAnchor(
        secondary_label=label,
        snapshot=snaps[-1],
    )
