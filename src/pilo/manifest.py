from dataclasses import dataclass
from pathlib import Path

from . import error
from . import fs
from . import paths

from .manifest_model import (
    ManifestEntry,
    ManifestAddEntry,
    ManifestRemoveEntry,
)

from .manifest_codec import (
    render_manifest_entry,
    parse_manifest_line,
    render_manifest_lines,
    load_manifest_entries,
)

from .manifest_store import (
    write_manifest_entries,
    write_manifest,
    commit_manifest_if_changed,
)

from .manifest_verify import (
    generate_manifest_entries,
    generate_manifest_lines,
    verify_manifest_lines,
)


MANIFEST_SUBSET_DOMAINS = {
    "pile": paths.StorageDomain.PILE,
    "collection": paths.StorageDomain.COLLECTION,
    "filing": paths.StorageDomain.FILING,
}


MANIFEST_DATASET_PATTERNS = {
    "pile": "/pile",
    "collection": "/static/collection",
    "filing": "/static/filing",
}


@dataclass(frozen=True)
class ManifestSubset:
    name: str
    root: Path
    manifest: Path


@dataclass(frozen=True)
class ManifestUpdatePlan:
    subsets: list[ManifestSubset]


def manifest_subset_domain(subset):
    try:
        return MANIFEST_SUBSET_DOMAINS[subset]
    except KeyError:
        error.fatal(f"invalid manifest subset: {subset}")


def manifest_subset_root(cx, subset):
    domain = manifest_subset_domain(subset)
    policy = cx.storage_policy(domain)
    return policy.root_path


def dataset_manifest_subset(dataset):
    if dataset.endswith(MANIFEST_DATASET_PATTERNS["pile"]):
        return "pile"
    for subset in ("collection", "filing"):
        pattern = MANIFEST_DATASET_PATTERNS[subset]
        if pattern in dataset:
            return subset
    return None


def build_manifest_update_plan(cx, subsets):
    def build(name):
        manifest = cx.admin_path / "manifest" / f"{name}.manifest"
        root = manifest_subset_root(cx, name)
        return ManifestSubset(name=name, root=root, manifest=manifest)

    resolved = [build(name) for name in subsets]
    return ManifestUpdatePlan(subsets=resolved)


def execute_manifest_update_plan(cx, plan):
    for subset in plan.subsets:
        fs.ensure_parent_dir(cx, subset.manifest)
        write_manifest(cx, subset.root, subset.manifest)
        msg = f"{subset.name} manifest update"
        commit_manifest_if_changed(cx, subset.manifest, msg)


def apply_manifest_mutations(entries, muts):
    by_path = {entry.path: entry for entry in entries}
    for mut in muts:
        if isinstance(mut, ManifestRemoveEntry):
            by_path.pop(mut.path, None)
        elif isinstance(mut, ManifestAddEntry):
            by_path[mut.entry.path] = mut.entry
    return [by_path[path] for path in sorted(by_path)]


def execute_manifest_mutations(cx, subset, manifest_path, muts):
    relevant = [mut for mut in muts if mut.subset == subset]
    entries = load_manifest_entries(manifest_path)
    updated = apply_manifest_mutations(entries, relevant)
    write_manifest_entries(cx, manifest_path, updated)
