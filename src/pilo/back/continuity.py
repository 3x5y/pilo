from dataclasses import dataclass

from .. import error
from .. import zfs


@dataclass(frozen=True)
class ContinuityAnchor:
    secondary_label: str
    snapshot: str


@dataclass(frozen=True)
class AgeingPlan:
    secondary_to_prune: list[str]
    secondary_to_release: list[ContinuityAnchor]
    primary_to_prune: list[str]
    primary_to_release: list[ContinuityAnchor]


def hold_tag(label: str) -> str:
    return f"pilo:{label}"


def parse_hold_tag(tag: str) -> str | None:
    prefix = "pilo:"
    if tag.startswith(prefix):
        return tag[len(prefix):]
    return None


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


def unheld_snapshots(dataset):
    result = []
    for name, refs in zfs.snapshots_userrefs(dataset):
        if refs > 0:
            break
        result.append(name)
    return result


def _guid_set(dataset):
    guids = set()
    for name, guid in zfs.snapshot_guids(dataset):
        guids.add(guid)
    return guids


def expired_secondary_anchors(cx, secondary_root):
    if not zfs.dataset_exists(secondary_root):
        return []

    primary_guids = _guid_set(cx.root_dataset)
    sec_guid_map = {
        name: guid
        for name, guid in zfs.snapshot_guids(secondary_root)
    }

    result = []
    for name, refs in zfs.snapshots_userrefs(secondary_root):
        guid = sec_guid_map.get(name)
        if guid is None:
            continue
        if guid in primary_guids:
            break
        if refs == 0:
            continue
        for snap, tag in zfs.list_holds(name):
            label = parse_hold_tag(tag)
            if label is not None:
                result.append(ContinuityAnchor(
                    secondary_label=label,
                    snapshot=name,
                ))
    return result


def primary_holds_to_release(cx, secondary_root, keep=1):
    label = label_for_secondary(cx, secondary_root)
    held = anchors(cx, label=label)
    if len(held) <= keep:
        return []
    return held[:-keep]


def ageing_plan(cx, secondary_root, keep=1):
    if keep < 1:
        error.fatal(f"keep must be >= 1, got {keep}")
    return AgeingPlan(
        secondary_to_prune=unheld_snapshots(secondary_root),
        secondary_to_release=expired_secondary_anchors(cx, secondary_root),
        primary_to_prune=unheld_snapshots(cx.root_dataset),
        primary_to_release=primary_holds_to_release(
            cx, secondary_root, keep=keep,
        ),
    )


def execute_ageing_plan(cx, secondary_root, plan):
    zfs.destroy_snapshots(plan.secondary_to_prune)
    for anchor in plan.secondary_to_release:
        zfs.release(hold_tag(anchor.secondary_label), anchor.snapshot)
    zfs.destroy_snapshots(plan.primary_to_prune)
    for anchor in plan.primary_to_release:
        zfs.release(hold_tag(anchor.secondary_label), anchor.snapshot)


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
