from dataclasses import dataclass
from pathlib import Path

from . import capture
from .. import checks
from .. import checksum
from .. import fs
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
    muts = ingest_plan_mutations(plan)
    return mutation.preview_execution_rendered(cx, muts)


def execute_ingest_plan(cx, plan):
    muts = ingest_plan_mutations(plan)
    mutation.execute_semantic_mutations(cx, muts)


def ingest_plan_mutations(plan):
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


def ingest_manifest_mutations(ops, pile_root):

    muts = []
    for op in ops:
        if op.action != "move":
            continue

        rel = op.dst.relative_to(pile_root)
        acquired = checksum.generate_checksum(op.dst)
        muts.append(
            manifest_model.ManifestAddEntry(
                subset="pile",
                entry=manifest_model.ManifestEntry(
                    checksum=acquired.checksum,
                    path=rel,
                )
            )
        )
    return muts


def ingest_execution_plan(cx, plan):
    manifest_path = cx.admin_path / "manifest/pile.manifest"
    manifest_step = ManifestStep(
        subset="pile",
        manifest_path=manifest_path,
        build_mutations=lambda:
            ingest_manifest_mutations(
                plan.ops,
                cx.pile_path,
            ),
    )
    return ExecutionPlan(
        semantic_mutations=ingest_plan_mutations(plan),
        manifest_steps=[manifest_step],
    )
