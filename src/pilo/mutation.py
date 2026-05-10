from dataclasses import dataclass
from pathlib import Path

from . import fs
from . import error
from . import manifest
from . import zfs


@dataclass(frozen=True)
class SemanticMutation:
    action: str
    src: Path | None
    dst: Path | None
    dataset: str


class exec_dispatch:

    @staticmethod
    def move(cx, mut):
        fs.safe_move(cx, mut.src, mut.dst)

    @staticmethod
    def copy(cx, mut):
        fs.safe_copy(cx, mut.src, mut.dst)

    @staticmethod
    def unlink(cx, mut):
        fs.safe_unlink(mut.src)

    @staticmethod
    def rmdir(cx, mut):
        fs.safe_rmdir(mut.src)


class render_dispatch:

    @staticmethod
    def move(mut):
        return f"move {mut.src} -> {mut.dst}"

    @staticmethod
    def copy(mut):
        return f"copy {mut.src} -> {mut.dst}"

    @staticmethod
    def unlink(mut):
        return f"unlink {mut.src}"

    @staticmethod
    def rmdir(mut):
        return f"rmdir {mut.src}"


def render_mutation(mut):
    func = getattr(render_dispatch, mut.action)
    return func(mut)


def render_mutations(mutations):
    return [render_mutation(m) for m in mutations]


def apply_semantic_mutation(cx, mut: SemanticMutation):

    try:
        func = getattr(exec_dispatch, mut.action)
    except AttributeError:
        error.fatal(f"unsupported mutation action: {mut.action}")

    func(cx, mut)


def execute_semantic_mutations(cx, mutations):
    datasets = {m.dataset for m in mutations}
    with zfs.writable_datasets(datasets):
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
