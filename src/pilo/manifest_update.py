from dataclasses import dataclass
from pathlib import Path

from . import fs
from . import manifest_policy
from . import manifest_store


@dataclass(frozen=True)
class ManifestSubset:
    name: str
    root: Path
    manifest: Path


@dataclass(frozen=True)
class ManifestUpdatePlan:
    subsets: list[ManifestSubset]


def build_manifest_update_plan(cx, subsets):
    def build(name):
        manifest = cx.admin_path / "manifest" / f"{name}.manifest"
        root = manifest_policy.manifest_subset_root(cx, name)
        return ManifestSubset(name=name, root=root, manifest=manifest)

    resolved = [build(name) for name in subsets]
    return ManifestUpdatePlan(subsets=resolved)


def execute_manifest_update_plan(cx, plan):
    for subset in plan.subsets:
        fs.ensure_parent_dir(cx, subset.manifest)
        manifest_store.write_manifest(cx, subset.root, subset.manifest)
        msg = f"{subset.name} manifest update"
        manifest_store.commit_manifest_if_changed(cx, subset.manifest, msg)
