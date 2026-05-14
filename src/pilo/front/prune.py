from dataclasses import dataclass
from pathlib import Path

from .. import mutation


@dataclass(frozen=True)
class PruneOp:
    path: Path
    dataset: str


@dataclass(frozen=True)
class PrunePlan:
    ops: list[PruneOp]


def build_prune_plan(root, dataset):
    keep = (
        root / "in",
        root / "out",
        root / "sort",
    )

    ops = []
    would_remove = set()

    def would_be_empty(path):
        for x in path.iterdir():
            if x not in would_remove:
                return False
        return True

    for path in sorted(root.rglob("*"), reverse=True):
        if path in keep:
            continue

        if path.is_dir() and would_be_empty(path):
            would_remove.add(path)
            op = PruneOp(path=path, dataset=dataset)
            ops.append(op)

    return PrunePlan(ops=ops)


def prune_mutations(plan):
    def build(op):
        return mutation.RmdirMutation(path=op.path,
                                      dataset=op.dataset)
    return [build(op) for op in plan.ops]


def preview_prune_plan(cx, plan):
    muts = prune_mutations(plan)
    return mutation.render_mutation_preview(cx, muts)


def execute_prune_plan(cx, ops):
    mut = prune_mutations(ops)
    mutation.execute_fs_mutations(cx, mut)
