from dataclasses import dataclass
from pathlib import Path

from .. import checks
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


def execute_replace_plan(cx, plan):
    muts = replace_plan_mutations(plan)
    mutation.execute_semantic_mutations(cx, muts)


def replace_plan_mutations(plan):
    def build(op):
        return mutation.SemanticMutation(action="copy",
                                src=op.src,
                                dst=op.dst.path,
                                dataset=op.dst.dataset)
    return [build(op) for op in plan.ops]


