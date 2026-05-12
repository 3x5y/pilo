from dataclasses import dataclass
from pathlib import Path


from .. import checks
from .. import error
from .. import fs
from .. import mutation
from .. import manifest_model
from .. import manifest_policy


@dataclass(frozen=True)
class PromoteOp:
    action: str
    src: Path
    dst: Path | None
    dataset: str


@dataclass(frozen=True)
class PromotePlan:
    ops: list[PromoteOp]


def build_promote_plan(cx):
    out_path = cx.pile_path / "out"

    ops = []

    if not out_path.is_dir():
        return None

    # validate top-level dirs
    for child in out_path.iterdir():
        if child.name not in ("collection", "filing"):
            error.fatal(f"invalid /out/ structure: {child.name}")

    # collect files

    col_dir = out_path / "collection"
    fil_dir = out_path / "filing"
    col_files = sorted(fs.iter_files(col_dir)) if col_dir.is_dir() else []
    fil_files = sorted(fs.iter_files(fil_dir)) if fil_dir.is_dir() else []
    if not col_files and not fil_files:
        error.fatal("/out/ directory empty")

    # validate files

    def validate_file(cx, src: Path, rel: Path):
        r = cx.resolve(rel)
        checks.require_dataset(r.dataset)
        checks.require_no_conflict(src, r.path)

    for f in col_files:
        rel = Path("collection") / f.relative_to(col_dir)
        validate_file(cx, f, rel)
        r = cx.resolve(rel)
        if not r.path.is_file():
            op = PromoteOp(action="copy",
                           src=f,
                           dst=r.path,
                           dataset=r.dataset)
            ops.append(op)
        op = PromoteOp(action="unlink",
                       src=f,
                       dst=None,
                       dataset=cx.pile_dataset)
        ops.append(op)

    for f in fil_files:
        rel = f.relative_to(fil_dir)
        if len(rel.parts) < 2:
            error.fatal("invalid filing structure")
        subset = rel.parts[0]
        subpath = Path(*rel.parts[1:])
        full_rel = Path("filing") / subset / subpath
        validate_file(cx, f, full_rel)
        r = cx.resolve(full_rel)
        if not r.path.is_file():
            op = PromoteOp(action="copy",
                           src=f,
                           dst=r.path,
                           dataset=r.dataset)
            ops.append(op)
        op = PromoteOp(action="unlink",
                       src=f,
                       dst=None,
                       dataset=cx.pile_dataset)
        ops.append(op)

    return PromotePlan(ops=ops)


def preview_promote_plan(cx, plan):
    muts = promote_plan_mutations(plan)
    return mutation.preview_execution_rendered(cx, muts)


def execute_promote_plan(cx, plan):
    muts = promote_plan_mutations(plan)
    mutation.execute_semantic_mutations(cx, muts)


def promote_plan_mutations(plan):
    def build(op):
        if op.action == "copy":
            return mutation.CopyMutation(
                src=op.src,
                dst=op.dst,
                dataset=op.dataset,
            )

        if op.action == "unlink":
            return mutation.UnlinkMutation(
                path=op.src,
                dataset=op.dataset,
            )
    return [build(op) for op in plan.ops]


def promote_manifest_mutations(ops, pile_root, collection_root, filing_root):

    muts = []

    for op in ops:
        if op.action == "copy":
            subset = manifest_policy.dataset_manifest_subset(op.dataset)
            if subset == "collection":
                rel = op.dst.relative_to(collection_root)
            elif subset == "filing":
                rel = op.dst.relative_to(filing_root)
            else:
                continue
            muts.append(
                manifest_model.ManifestAddEntry(
                    subset=subset,
                    entry=manifest_model.ManifestEntry(
                        checksum=fs.sha256_file(op.dst),
                        path=rel,
                    )
                )
            )

        elif op.action == "unlink":
            rel = op.src.relative_to(pile_root)
            muts.append(
                manifest_model.ManifestRemoveEntry(
                    subset="pile",
                    path=rel,
                )
            )

    return muts
