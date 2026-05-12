from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


from . import manifest_mutation
from . import mutation_exec


class ExecutionPhase(Enum):
    PREFLIGHT = auto()
    MUTATION = auto()
    MANIFEST = auto()


@dataclass(frozen=True)
class ExecutionPlan:
    semantic_mutations: list = field(default_factory=list)
    manifest_steps: list = field(default_factory=list)


@dataclass(frozen=True)
class ManifestOperation:
    subset: str
    manifest_path: Path
    mutations: list


@dataclass(frozen=True)
class ManifestStep:
    subset: str
    manifest_path: Path
    build_mutations: Callable[[], list]


def execute_plan(cx, plan):

    if plan.semantic_mutations:
        mutation_exec.execute_semantic_mutations(cx, plan.semantic_mutations)

    for step in plan.manifest_steps:
        muts = step.build_mutations()
        manifest_mutation.execute_manifest_mutations(
            cx,
            step.subset,
            step.manifest_path,
            muts,
        )
