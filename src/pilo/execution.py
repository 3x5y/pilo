from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


from . import error
from . import fs
from . import manifest_mutation
from . import mutation_exec


class ExecutionPhase(Enum):
    PREFLIGHT = auto()
    FILESYSTEM = auto()
    MANIFEST = auto()


@dataclass(frozen=True)
class ExecutionPlan:
    preflight_steps: list = field(default_factory=list)
    filesystem_steps: list = field(default_factory=list)
    manifest_steps: list = field(default_factory=list)


@dataclass(frozen=True)
class ManifestStep:
    subset: str
    manifest_path: Path
    build_mutations: Callable[[], list]


@dataclass(frozen=True)
class VerifyChecksumStep:
    path: Path
    expected_checksum: str


def execute_plan(cx, plan):

    execute_preflight_steps(plan.preflight_steps)

    if plan.filesystem_steps:
        mutation_exec.execute_fs_mutations(cx, plan.filesystem_steps)

    for step in plan.manifest_steps:
        muts = step.build_mutations()
        manifest_mutation.execute_manifest_mutations(
            cx,
            step.subset,
            step.manifest_path,
            muts,
        )


def execute_verify_checksum_step(step):
    actual = fs.sha256_file(step.path)
    if actual != step.expected_checksum:
        error.fatal(
            f"checksum verification failed: "
            f"{step.path}"
        )


def execute_preflight_steps(steps):
    for step in steps:
        if isinstance(step, VerifyChecksumStep):
            execute_verify_checksum_step(step)
            continue
        raise RuntimeError(
            f"unsupported preflight step: "
            f"{type(step).__name__}"
        )
