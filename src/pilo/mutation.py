from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

from . import error
from . import fs
from . import manifest
from . import zfs

from .mutation_events import OperationEvent
from .mutation_types import (
    CopyMutation,
    MoveMutation,
    RmdirMutation,
    UnlinkMutation,
    SemanticMutation,
)

from .mutation_exec import (
    MutationExecutor,
    LiveExecutor,
    execute_mutation,
    execute_mutations,
    execute_semantic_mutations,
)


class PreviewExecutor(MutationExecutor):
    requires_write_access = False

    def __init__(self, cx):
        super().__init__(cx)
        self.events = []

    def apply(self, mut):
        e = event_for_mutation(mut)
        self.events.append(e)


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
    return executor.events


def preview_execution_rendered(cx, mutations):
    events = preview_execution(cx, mutations)
    return render_events(events)


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


def event_for_mutation(mut):

    if isinstance(mut, MoveMutation):
        return OperationEvent(
            kind="move",
            src=mut.src,
            dst=mut.dst,
            dataset=mut.dataset,
        )

    if isinstance(mut, CopyMutation):
        return OperationEvent(
            kind="copy",
            src=mut.src,
            dst=mut.dst,
            dataset=mut.dataset,
        )

    if isinstance(mut, UnlinkMutation):
        return OperationEvent(
            kind="unlink",
            src=mut.path,
            dst=None,
            dataset=mut.dataset,
        )

    if isinstance(mut, RmdirMutation):
        return OperationEvent(
            kind="rmdir",
            src=mut.path,
            dst=None,
            dataset=mut.dataset,
        )

    error.fatal(
        f"unsupported mutation type: {type(mut).__name__}"
    )


def render_event(ev):
    if ev.dst is None:
        return f"{ev.kind} {ev.src}"
    return f"{ev.kind} {ev.src} -> {ev.dst}"


def render_mutation(mut):
    ev = event_for_mutation(mut)
    return render_event(ev)


def render_events(events):
    return [render_event(ev) for ev in events]
