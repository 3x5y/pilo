import sys
from dataclasses import dataclass
from pathlib import Path

from .. import checks
from .. import checksum
from .. import continuity
from .. import error
from .. import manifest_model
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
        mutations.append(
            mutation.MoveMutation(
                src=op.src.path,
                dst=op.dst.path,
                dataset=op.src.dataset,
            )
        )
    return mutations


def rewrite_manifest_mutations(plan, pile_root, verified):

    mappings = []

    for op in plan.ops:
        src_rel = op.src.path.relative_to(pile_root)
        dst_rel = op.dst.path.relative_to(pile_root)
        m = continuity.ContinuityMapping(
            src_subset="pile",
            dst_subset="pile",
            src=src_rel,
            dst=dst_rel,
        )
        mappings.append(m)

    transfers = continuity.build_continuity_transfers(
        mappings,
        verified,
    )

    return continuity.continuity_manifest_mutations(transfers)


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


def is_preview_mode(cx):
    return (
        len(cx.args) >= 1
        and cx.args[0] == "--preview"
    )


def rewrite_script_args(cx):
    if is_preview_mode(cx):
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

        lines = [
            f"#version {SCRIPT_VERSION}"
        ]

        for op in ops:
            lines.append(
                "\t".join([
                    op.kind,
                    str(op.src),
                    str(op.dst),
                ])
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


def rewrite_execution_plan(cx, plan, entries):
    index = manifest_model.as_manifest_index(entries)
    verified = rewrite_verified_checksums(plan, cx.pile_path, index)
    manifest_path = cx.admin_path / "manifest/pile.manifest"
    manifest_step = ManifestStep(
        subset="pile",
        manifest_path=manifest_path,
        build_mutations=lambda:
            rewrite_manifest_mutations(
                plan,
                cx.pile_path,
                verified,
            ),
    )
    preflight_steps= rewrite_preflight_steps(plan, cx.pile_path, entries)
    return ExecutionPlan(
        preflight_steps=preflight_steps,
        filesystem_steps=rewrite_plan_mutations(plan),
        manifest_steps=[manifest_step],
    )


def rewrite_preflight_steps(plan, pile_root, entries):

    index = manifest_model.as_manifest_index(entries)
    steps = []

    for op in plan.ops:
        src_rel = op.src.path.relative_to(pile_root)
        existing = index.require(src_rel)
        steps.append(
            VerifyChecksumStep(
                path=op.src.path,
                expected_checksum=
                    existing.checksum,
            )
        )
    return steps


def rewrite_verified_checksums(plan, pile_root, entries):
    return rewrite_acquire_checksums(plan, pile_root, entries)


def rewrite_acquire_checksums(plan, pile_root, entries):
    verified = []
    for op in plan.ops:
        src_rel = op.src.path.relative_to(pile_root)
        existing = entries.require(src_rel)
        verified_item = checksum.verify_checksum(
            op.src.path,
            existing.checksum,
        )

        verified.append(
            manifest_model.ProvenancedChecksum(
                path=src_rel,
                checksum=verified_item.checksum,
                provenance=verified_item.provenance,
            )
        )
    return manifest_model.VerifiedChecksumIndex(verified)
