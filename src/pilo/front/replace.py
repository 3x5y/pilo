from dataclasses import dataclass
from pathlib import Path

from .. import checks
from .. import fs
from .. import manifest_model
from .. import mutation
from .. import paths


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
    muts = replace_plan_mutations(plan)
    return mutation.preview_execution_rendered(cx, muts)


def execute_replace_plan(cx, plan):
    muts = replace_plan_mutations(plan)
    mutation.execute_semantic_mutations(cx, muts)


def replace_plan_mutations(plan):
    def build(op):
        return mutation.CopyMutation(src=op.src,
                                     dst=op.dst.path,
                                     dataset=op.dst.dataset)
    return [build(op) for op in plan.ops]


def replace_manifest_mutations(plan, pile_root):
    muts = []
    for op in plan.ops:
        rel = op.dst.path.relative_to(pile_root)
        muts.append(
            manifest_model.ManifestAddEntry(
                subset="pile",
                entry=manifest_model.ManifestEntry(
                    checksum=fs.sha256_file(op.src),
                    path=rel,
                )
            )
        )
    return muts
