from dataclasses import dataclass
from pathlib import Path

from .. import checks
from .. import paths
from . import continuity
from . import manifest
from ..front import mutation
from .execution import (
    ExecutionPlan,
    ManifestStep,
)


@dataclass(frozen=True)
class ReplaceOp:
    src: Path
    dst: paths.Resolved


@dataclass(frozen=True)
class ReplacePlan:
    ops: list[ReplaceOp]


def build_replace_plan(cx, src, dst_rel):
    checks.require_file(src)
    resolved = cx.resolve(dst_rel)
    checks.require_file(resolved.path)
    checks.require_dataset(resolved.dataset)
    op = ReplaceOp(src=src, dst=resolved)
    return ReplacePlan(ops=[op])


def preview_replace_plan(cx, plan):
    muts = build_fs_mutations(plan)
    return mutation.render_mutation_preview(cx, muts)


def execute_replace_plan(cx, plan):
    muts = build_fs_mutations(plan)
    mutation.execute_fs_mutations(cx, muts)


def build_fs_mutations(plan):
    def build(op):
        return mutation.CopyMutation(src=op.src,
                                     dst=op.dst.path,
                                     dataset=op.dst.dataset)
    return [build(op) for op in plan.ops]


def build_manifest_mutations(plan, pile_root):
    index = build_checksum_index(plan.ops, pile_root)
    paths = [op.dst.path.relative_to(pile_root) for op in plan.ops]
    return manifest.build_pile_additions(paths, index)


def build_checksum_index(ops, pile_root):
    pairs = [(op.dst.path.relative_to(pile_root), op.src)
             for op in ops]
    checksums = continuity.acquire_generated_checksums(pairs)
    return manifest.as_checksum_index(checksums)


def build_exec_plan(cx, plan):
    manifest_path = cx.admin_path / "manifest/pile.manifest"
    manifest_step = ManifestStep(
        subset="pile",
        manifest_path=manifest_path,
        build_mutations=lambda:build_manifest_mutations(plan, cx.pile_path)
    )
    return ExecutionPlan(
        filesystem_steps=build_fs_mutations(plan),
        manifest_steps=[manifest_step],
    )
