import sys
from dataclasses import dataclass
from pathlib import Path

from .. import checks
from .. import continuity
from .. import error
from .. import manifest_model
from .. import manifest_policy
from .. import mutation
from .. import paths
from .. import policy
from ..execution import (
    ExecutionPlan,
    ManifestStep,
    VerifyChecksumStep,
)


SCRIPT_VERSION = 1


@dataclass(frozen=True)
class RewriteOp:
    kind: str
    src: Path
    dst: Path | None = None


@dataclass(frozen=True)
class ResolvedRewriteOp:
    op: RewriteOp
    src: paths.Resolved
    dst: paths.Resolved | None


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
        kind = parts[0]

        if kind == "mv":

            if len(parts) != 3:
                error.fatal(f"invalid command: {line}")

            _, src, dst = parts

            src_p = Path(src)
            dst_p = Path(dst)

            policy.require_relative_path(src_p)
            policy.require_relative_path(dst_p)

            op = RewriteOp(kind="mv", src=src_p, dst=dst_p)
            ops.append(op)

        elif kind == "rm":

            if len(parts) != 2:
                error.fatal(f"invalid command: {line}")

            _, src = parts

            src_p = Path(src)
            policy.require_relative_path(src_p)
            op = RewriteOp(kind="rm", src=src_p)
            ops.append(op)

        else:
            error.fatal(f"unsupported operation: '{kind}'")

    return ops


def resolve_rewrite_op(cx, op: RewriteOp):
    src = cx.resolve(op.src)
    dst = cx.resolve(op.dst) if op.dst is not None else None
    return ResolvedRewriteOp(src=src, dst=dst, op=op)


def validate_move_op(cx, op):
    policy.require_same_domain(op.op.src, op.op.dst)
    checks.require_file(op.src.path)
    checks.require_no_conflict(op.src.path, op.dst.path)


def validate_remove_op(cx, op):
    checks.require_file(op.src.path)


def validate_rewrite_op(cx, op):
    if op.op.kind == "mv":
        validate_move_op(cx, op)
    elif op.op.kind == "rm":
        validate_remove_op(cx, op)
    else:
        error.fatal(
            f"unsupported rewrite op: "
            f"{op.op.kind}"
        )


def validate_rewrite_ops(cx, ops):
    seen_src = set()
    seen_dst = set()

    for op in ops:
        if op.op.src in seen_src:
            error.fatal(f"duplicate source in script: {op.op.src}")
        seen_src.add(op.op.src)
        if op.op.dst is not None:
            if op.op.dst in seen_dst:
                error.fatal(f"destination conflict in script: {op.op.dst}")
            seen_dst.add(op.op.dst)
        validate_rewrite_op(cx, op)


def build_rewrite_plan(cx, ops):
    resolved = [resolve_rewrite_op(cx, op) for op in ops]
    validate_rewrite_ops(cx, resolved)
    return RewritePlan(ops=resolved)


def preview_rewrite_plan(cx, plan):
    muts = build_fs_mutations(plan)
    return mutation.render_mutation_preview(cx, muts)


def execute_rewrite_plan(cx, plan):
    muts = build_fs_mutations(plan)
    mutation.execute_fs_mutations(cx, muts)


def build_fs_mutations(plan):
    mutations = []
    for op in plan.ops:
        if op.op.kind == "mv":
            mutations.append(
                mutation.MoveMutation(
                    src=op.src.path,
                    dst=op.dst.path,
                    dataset=op.src.dataset,
                )
            )
        elif op.op.kind == "rm":
            mutations.append(
                mutation.UnlinkMutation(
                    path=op.src.path,
                    dataset=op.src.dataset,
                )
            )
        else:
            error.fatal(
                f"unsupported rewrite op: "
                f"{op.op.kind}"
            )
    return mutations


def build_manifest_mutations(ops, pile_root, verified):

    muts = []
    for op in ops:
        src_rel = op.src.path.relative_to(pile_root)
        if op.op.kind == "mv":
            dst_rel = op.dst.path.relative_to(pile_root)
            mapping = continuity.ContinuityMapping(
                src_subset="pile",
                dst_subset="pile",
                src=src_rel,
                dst=dst_rel,
            )
            tm = continuity.build_transfer_mutations([mapping], verified)
            muts.extend(tm)
        elif op.op.kind == "rm":
            muts.append(manifest_policy.build_removal("pile", src_rel))
        else:
            error.fatal(
                f"unsupported rewrite op: "
                f"{op.op.kind}"
            )
    return muts


def build_manifest_mutations(ops, pile_root, verified):

    mappings = []
    removals = []

    for op in ops:
        src_rel = op.src.path.relative_to(pile_root)
        if op.op.kind == "mv":
            dst_rel = op.dst.path.relative_to(pile_root)
            mappings.append(
                continuity.ContinuityMapping(
                    src_subset="pile",
                    dst_subset="pile",
                    src=src_rel,
                    dst=dst_rel,
                )
            )
        elif op.op.kind == "rm":
            removals.append(
                continuity.ContinuityRemoval(
                    subset="pile",
                    path=src_rel,
                )
            )
        else:
            error.fatal(
                f"unsupported rewrite operation: "
                f"{op.op.kind}"
            )

    muts = continuity.build_transfer_mutations(mappings, verified)
    muts.extend(continuity.build_removal_mutations(removals))

    return muts


def load_rewrite_lines(cx):
    args = rewrite_script_args(cx)
    if args:
        arg = args[0]
        path = Path(arg)
        if path.is_file():
            return path.read_text().splitlines()
        return arg.splitlines()
    return sys.stdin.read().splitlines()


def load_rewrite_script(cx):
    lines = load_rewrite_lines(cx)
    return RewriteScript.from_lines(lines)


def has_delete_flag(cx):
    return "--delete" in cx.args


def require_delete_permission(cx, ops):

    if has_delete_flag(cx):
        return

    for op in ops:
        if op.op.kind == "rm":
            error.fatal(
                "rewrite contains removals; "
                "rerun with --delete"
            )


def is_preview_mode(cx):
    return (
        len(cx.args) >= 1
        and cx.args[0] == "--preview"
    )


def rewrite_script_args(cx):
    if is_preview_mode(cx):
        return cx.args[1:]
    if has_delete_flag(cx):
        return cx.args[1:]
    return cx.args


@dataclass(frozen=True)
class RewriteScript:
    lines: list[str]

    @classmethod
    def from_lines(Class, lines):
        return Class(lines=list(lines))

    def parse_ops(self):
        return parse_rewrite_ops(self.body_lines())

    @classmethod
    def from_ops(cls, ops):
        lines = [f"#version {SCRIPT_VERSION}"]
        for op in ops:
            if op.kind == "mv":
                lines.append(
                    "\t".join([
                        op.kind,
                        str(op.src),
                        str(op.dst),
                    ])
                )
            elif op.kind == "rm":
                lines.append(
                    "\t".join([
                        op.kind,
                        str(op.src),
                    ])
                )
            else:
                error.fatal(
                    f"unsupported rewrite operation: "
                    f"{op.kind}"
                )

        return cls(lines=lines)

    def version(self):

        if not self.lines:
            return None

        line = self.lines[0].strip()

        if not line.startswith("#version "):
            return None

        parts = line.split()

        if len(parts) != 2:
            error.fatal(f"invalid version header: {line}")

        try:
            return int(parts[1])
        except ValueError:
            error.fatal(f"invalid version header: {line}")

    def body_lines(self):
        version = self.version()
        if version is None:
            return self.lines
        if version != SCRIPT_VERSION:
            error.fatal(f"unsupported script version: {version}")
        return self.lines[1:]

    def render_lines(self):
        return list(self.lines)

    def render_text(self):
        return "\n".join(self.render_lines())


def build_exec_plan(cx, plan, entries):
    verified = build_checksum_index(plan.ops, cx.pile_path, entries)
    manifest_path = cx.admin_path / "manifest/pile.manifest"
    manifest_step = ManifestStep(
        subset="pile",
        manifest_path=manifest_path,
        build_mutations=lambda:
            build_manifest_mutations(
                plan.ops,
                cx.pile_path,
                verified,
            ),
    )
    preflight_steps = build_preflight_steps(plan, cx.pile_path, entries)
    return ExecutionPlan(
        preflight_steps=preflight_steps,
        filesystem_steps=build_fs_mutations(plan),
        manifest_steps=[manifest_step],
    )


def build_preflight_steps(plan, pile_root, entries):

    index = manifest_model.as_manifest_index(entries)
    steps = []

    for op in plan.ops:
        src_rel = op.src.path.relative_to(pile_root)
        existing = index.require(src_rel)
        step = VerifyChecksumStep(
            path=op.src.path,
            expected_checksum=existing.checksum,
        )
        steps.append(step)
    return steps


def build_checksum_index(ops, pile_root, entries):
    index = manifest_model.as_manifest_index(entries)
    pairs = []
    for op in ops:
        pairs.append((op.src.path.relative_to(pile_root), op.src.path))
    return continuity.acquire_verified_checksums(pairs, index)
