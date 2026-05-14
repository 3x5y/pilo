from dataclasses import dataclass
from pathlib import Path

from . import capture
from .. import checks
from .. import checksum
from .. import continuity
from .. import manifest_model
from .. import mutation
from ..execution import (
    ExecutionPlan,
    ManifestStep,
)


@dataclass(frozen=True)
class IngestOp:
    src: Path
    dst: Path
    dataset: str
    action: str


@dataclass(frozen=True)
class IngestPlan:
    ops: list[IngestOp]


def build_ingest_plan(cx, files):
    ops = []
    for src in files:
        rel = src.relative_to(cx.intake_path)
        dst = cx.pile_path / "in" / rel
        checks.require_no_conflict(src, dst)
        if dst.exists():
            action = 'noop'
        else:
            action = 'move'
        ops.append(IngestOp(
            src=src,
            dst=dst,
            dataset=cx.pile_dataset,
            action=action
        ))
    return IngestPlan(ops=ops)


def preview_ingest_plan(cx, plan):
    muts = build_fs_mutations(plan)
    return mutation.render_mutation_preview(cx, muts)


def execute_ingest_plan(cx, plan):
    muts = build_fs_mutations(plan)
    mutation.execute_fs_mutations(cx, muts)


def build_fs_mutations(plan):
    muts = []
    for op in plan.ops:
        if op.action == "move":
            muts.append(
                mutation.MoveMutation(
                    src=op.src,
                    dst=op.dst,
                    dataset=op.dataset,
                )
            )
        elif op.action == "noop":
            muts.append(
                mutation.UnlinkMutation(
                    path=op.src,
                    dataset=op.dataset,
                )
            )
    return muts


def ingestible_capture_files(files):
    for path in files:
        if path.name == capture.CAPTURE_MANIFEST:
            continue
        yield path


def build_manifest_mutations(ops, pile_root):

    pairs = [(op.dst.relative_to(pile_root), op.dst)
            for op in ops if op.action == "move"]
    checksums = continuity.acquire_generated_checksums(pairs)
    index = manifest_model.as_checksum_index(checksums)
    muts = []
    for op in ops:
        if op.action != "move":
            continue

        rel = op.dst.relative_to(pile_root)
        item = index.require(rel)
        muts.append(
            manifest_model.ManifestAddEntry(
                subset="pile",
                entry=manifest_model.ManifestEntry(
                    checksum=item.checksum,
                    path=rel,
                )
            )
        )
    return muts


def build_exec_plan(cx, plan):
    manifest_path = cx.admin_path / "manifest/pile.manifest"
    manifest_step = ManifestStep(
        subset="pile",
        manifest_path=manifest_path,
        build_mutations=lambda:
            build_manifest_mutations(
                plan.ops,
                cx.pile_path,
            ),
    )
    return ExecutionPlan(
        filesystem_steps=build_fs_mutations(plan),
        manifest_steps=[manifest_step],
    )
