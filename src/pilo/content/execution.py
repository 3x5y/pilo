from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


from . import manifest
from . import mutation


@dataclass(frozen=True)
class ExecutionPlan:
    filesystem_steps: list = field(default_factory=list)
    manifest_steps: list = field(default_factory=list)


@dataclass(frozen=True)
class ManifestStep:
    subset: str
    manifest_path: Path
    build_mutations: Callable[[], list]


def execute_plan(cx, plan):

    if plan.filesystem_steps:
        mutation.execute_fs_mutations(cx, plan.filesystem_steps)

    for step in plan.manifest_steps:
        muts = step.build_mutations()
        manifest.execute_manifest_mutations(
            cx,
            step.subset,
            step.manifest_path,
            muts,
        )