from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path

from . import error
from . import fs
from . import manifest_policy
from . import manifest_update
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

from .mutation_preview import (
    PreviewExecutor,
    preview_execution,
    preview_execution_rendered,
    event_for_mutation,
)

from .mutation_render import (
    render_event,
    render_events,
    render_mutation,
    render_mutations,
)


def mutation_manifest_domains(mutations):
    domains = set()
    for mut in mutations:
       subset = manifest_policy.dataset_manifest_subset(mut.dataset)
       if subset:
           domains.add(subset)
    return domains


def build_manifest_plan_for_mutations(cx, mutations):
    domains = sorted(mutation_manifest_domains(mutations))
    return manifest_update.build_manifest_update_plan(cx, domains)


