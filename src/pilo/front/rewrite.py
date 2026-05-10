from dataclasses import dataclass
from pathlib import Path

from .. import checks
from .. import error
from .. import mutation
from .. import paths
from .. import policy


@dataclass(frozen=True)
class RewriteOp:
    kind: str
    src: Path
    dst: Path


@dataclass(frozen=True)
class ResolvedRewriteOp:
    op: RewriteOp
    src: paths.Resolved
    dst: paths.Resolved


@dataclass(frozen=True)
class RewritePlan:
    ops: list[ResolvedRewriteOp]


def parse_rewrite_ops(lines):
    ops = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        parts = line.split("\t")

        if len(parts) != 3:
            error.fatal(f"invalid command: {line}")

        kind, src, dst = parts

        if kind != "mv":
            error.fatal(f"unsupported operation: '{kind}'")

        src_p = Path(src)
        dst_p = Path(dst)

        policy.require_relative_path(src_p)
        policy.require_relative_path(dst_p)

        op = RewriteOp( kind=kind, src=src_p, dst=dst_p)
        ops.append(op)

    return ops


def resolve_rewrite_op(cx, op: RewriteOp):
    src = cx.resolve(op.src)
    dst = cx.resolve(op.dst)
    return ResolvedRewriteOp(src=src, dst=dst, op=op)


def validate_rewrite_op(cx, op: ResolvedRewriteOp):
    policy.require_same_domain(op.op.src, op.op.dst)
    checks.require_file(op.src.path)
    checks.require_no_conflict(op.src.path, op.dst.path)


def validate_rewrite_ops(cx, ops):
    seen_src = set()
    seen_dst = set()

    for op in ops:
        if op.op.src in seen_src:
            error.fatal(f"duplicate source in script: {op.op.src}")
        if op.op.dst in seen_dst:
            error.fatal(f"destination conflict in script: {op.op.dst}")
        seen_src.add(op.op.src)
        seen_dst.add(op.op.dst)
        validate_rewrite_op(cx, op)


def build_rewrite_plan(cx, ops):
    resolved = [resolve_rewrite_op(cx, op) for op in ops]
    validate_rewrite_ops(cx, resolved)
    return RewritePlan(ops=resolved)


def preview_rewrite_plan(cx, plan):
    muts = rewrite_plan_mutations(plan)
    return mutation.preview_execution_rendered(cx, muts)


def execute_rewrite_plan(cx, plan):
    muts = rewrite_plan_mutations(plan)
    mutation.execute_semantic_mutations(cx, muts)


def rewrite_plan_mutations(plan):
    mutations = []

    for op in plan.ops:
        dst_exists = op.dst.path.exists()

        if dst_exists:
            # currently unimplemented; throw error
            1/0
            mutations.append(
                mutation.UnlinkMutation(
                    src=op.src.path,
                    dst=None,
                    dataset=op.src.dataset,
                )
            )
        else:
            mutations.append(
                mutation.MoveMutation(
                    src=op.src.path,
                    dst=op.dst.path,
                    dataset=op.src.dataset,
                )
            )
    return mutations
