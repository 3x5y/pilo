from dataclasses import dataclass
from pathlib import Path

from . import manifest_codec
from . import manifest_model
from . import manifest_store


def apply_manifest_mutations(entries, muts):
    by_path = {entry.path: entry for entry in entries}
    for mut in muts:
        if isinstance(mut, manifest_model.ManifestRemoveEntry):
            by_path.pop(mut.path, None)
        elif isinstance(mut, manifest_model.ManifestAddEntry):
            by_path[mut.entry.path] = mut.entry
    return [by_path[path] for path in sorted(by_path)]


def execute_manifest_mutations(cx, subset, manifest_path, muts):
    relevant = [mut for mut in muts if mut.subset == subset]
    entries = manifest_codec.load_manifest_entries(manifest_path)
    updated = apply_manifest_mutations(entries, relevant)
    manifest_store.write_manifest_entries(cx, manifest_path, updated)
