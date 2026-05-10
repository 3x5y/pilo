from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

from . import error
from . import fs
from . import manifest
from . import zfs


@dataclass(frozen=True)
class SemanticMutation:
    action: str
    src: Path | None
    dst: Path | None
    dataset: str


@dataclass(frozen=True)
class MoveMutation:
    src: Path
    dst: Path
    dataset: str


@dataclass(frozen=True)
class CopyMutation:
    src: Path
    dst: Path
    dataset: str


@dataclass(frozen=True)
class UnlinkMutation:
    path: Path
    dataset: str


@dataclass(frozen=True)
class RmdirMutation:
    path: Path
    dataset: str


class MutationExecutor:

    def __init__(self, cx):
        self.cx = cx

    def apply(self, mut):
        raise NotImplementedError


class LiveExecutor(MutationExecutor):
    requires_write_access = True
    def apply(self, mut):
        apply_semantic_mutation(self.cx, mut)


class PreviewExecutor(MutationExecutor):
    requires_write_access = False

    def __init__(self, cx):
        super().__init__(cx)
        self.rendered = []

    def apply(self, mut):
        self.rendered.append(
            render_mutation(mut)
        )


class exec_dispatch:

    @staticmethod
    def move(cx, mut :MoveMutation):
        fs.safe_move(cx, mut.src, mut.dst)

    @staticmethod
    def copy(cx, mut: CopyMutation):
        fs.safe_copy(cx, mut.src, mut.dst)

    @staticmethod
    def unlink(cx, mut: UnlinkMutation):
        fs.safe_unlink(mut.path)

    @staticmethod
    def rmdir(cx, mut: RmdirMutation):
        fs.safe_rmdir(mut.path)


class render_dispatch:

    @staticmethod
    def move(mut: MoveMutation):
        return f"move {mut.src} -> {mut.dst}"

    @staticmethod
    def copy(mut: CopyMutation):
        return f"copy {mut.src} -> {mut.dst}"

    @staticmethod
    def unlink(mut: UnlinkMutation):
        return f"unlink {mut.path}"

    @staticmethod
    def rmdir(mut: RmdirMutation):
        return f"rmdir {mut.path}"


def mutation_kind(mut):
    name = type(mut).__name__

    if name.endswith("Mutation"):
        name = name[:-8]

    return name.lower()


def render_mutation(mut):
    kind = mutation_kind(mut)
    func = getattr(render_dispatch, kind)
    return func(mut)


def render_mutations(mutations):
    return [render_mutation(m) for m in mutations]


def preview_mutations(mutations):
    return render_mutations(mutations)


def preview_execution(cx, mutations):
    executor = PreviewExecutor(cx)
    execute_mutations(executor, mutations)
    return executor.rendered


def apply_semantic_mutation(cx, mut: SemanticMutation):
    kind = mutation_kind(mut)
    try:
        func = getattr(exec_dispatch, kind)
    except AttributeError:
        error.fatal(f"unsupported mutation type: {type(mut).__name__}")
    func(cx, mut)


def execute_mutations(executor, mutations):

    if executor.requires_write_access:
        datasets = {m.dataset for m in mutations}
        context = zfs.writable_datasets(datasets)
    else:
        context = nullcontext()

    with context:
        for mut in mutations:
            executor.apply(mut)


def execute_semantic_mutations(cx, mutations):
    executor = LiveExecutor(cx)
    execute_mutations(executor, mutations)


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
