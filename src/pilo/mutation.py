from dataclasses import dataclass
from pathlib import Path

from . import fs
from . import error
from . import manifest


@dataclass(frozen=True)
class SemanticMutation:
    action: str
    src: Path | None
    dst: Path | None
    dataset: str


def apply_semantic_mutation(cx, mut: SemanticMutation):
    if mut.action == "move":
        fs.safe_move(cx, mut.src, mut.dst)
        return
    if mut.action == "copy":
        fs.safe_copy(cx, mut.src, mut.dst)
        return
    if mut.action == "unlink":
        fs.safe_unlink(mut.src)
        return
    if mut.action == "rmdir":
        fs.safe_rmdir(mut.src)
        return
    error.fatal(f"unsupported mutation action: {mut.action}")


def execute_semantic_mutations(cx, mutations):
    datasets = {m.dataset for m in mutations}
    with fs.writable_datasets(datasets):
        for mut in mutations:
            apply_semantic_mutation(cx, mut)


def mutation_manifest_domains(mutations):
    domains = set()
    for mut in mutations:
       subset = manifest.dataset_manifest_subset(mut.dataset)
       if subset:
           domains.add(subset)
    return domains


def build_manifest_plan_for_mutations(cx, mutations):
    domains = sorted(mutation_manifest_domains(mutations))
    return manifest.build_manifest_update_plan(cx, domains)
