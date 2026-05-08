from dataclasses import dataclass
from pathlib import Path

from .. import mutation
from .. import validation


@dataclass(frozen=True)
class IngestOp:
    src: Path
    dst: Path
    dataset: str
    action: str


def build_ingest_ops(cx, files):
    ops = []
    for src in files:
        rel = src.relative_to(cx.intake_path)
        dst = cx.pile_path / "in" / rel
        validation.require_no_conflict(src, dst)
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
    return ops


def execute_ingest_ops(cx, ops):
    muts = ingest_plan_mutations(ops)
    mutation.execute_semantic_mutations(cx, muts)


def ingest_plan_mutations(ops):
    muts = []
    for op in ops:
        if op.action == "move":
            muts.append(
                mutation.SemanticMutation(
                    action="move",
                    src=op.src,
                    dst=op.dst,
                    dataset=op.dataset,
                )
            )
        elif op.action == "noop":
            muts.append(
                mutation.SemanticMutation(
                    action="unlink",
                    src=op.src,
                    dst=None,
                    dataset=op.dataset,
                )
            )
    return muts