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
    manifest_operations: list = field(default_factory=list)


@dataclass(frozen=True)
class ManifestOperation:
    subset: str
    manifest_path: Path
    mutations: list


def execute_plan(cx, plan):

    if plan.semantic_mutations:
        mutation_exec.execute_semantic_mutations(cx, plan.semantic_mutations)

    for op in plan.manifest_operations:
        manifest_mutation.execute_manifest_mutations(
            cx,
            op.subset,
            op.manifest_path,
            op.mutations,
        )
