from dataclasses import dataclass
from pathlib import Path


from .. import checks
from .. import error
from .. import fs
from . import manifest
from . import mutation
from .execution import (
    ExecutionPlan,
    ManifestStep,
    VerifyChecksumStep,
)


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
    muts = build_fs_mutations(plan)
    return mutation.render_mutation_preview(cx, muts)


def execute_promote_plan(cx, plan):
    muts = build_fs_mutations(plan)
    mutation.execute_fs_mutations(cx, muts)


def build_fs_mutations(plan):
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


def build_manifest_mutations(
    ops,
    pile_root,
    collection_root,
    filing_root,
    verified,
):
    mappings = promote_continuity_mappings(
        ops,
        pile_root,
        collection_root,
        filing_root,
    )
    return manifest.build_transfer_mutations(mappings, verified)


def build_preflight_steps(ops, pile_root, entries):

    index = manifest.as_manifest_index(entries)
    steps = []

    for op in ops:
        if op.action != "copy":
            continue
        rel = op.src.relative_to(pile_root)
        existing = index.require(rel)
        step = VerifyChecksumStep(
            path=op.src,
            expected_checksum=existing.checksum,
        )
        steps.append(step)
    return steps


def build_manifest_steps(cx, plan, pile_entries, verified):

    def build(subset):
        manifest_path =  cx.admin_path / "manifest" / f"{subset}.manifest"
        build_mutations = lambda: build_manifest_mutations(
            plan.ops,
            cx.pile_path,
            cx.static_path / "collection",
            cx.static_path / "filing",
            verified
        )
        return ManifestStep(subset, manifest_path, build_mutations)

    subsets = ("pile", "collection", "filing")
    return [build(x) for x in subsets]


def build_exec_plan(cx, plan, pile_entries):
    verified = build_checksum_index(plan.ops, cx.pile_path, pile_entries)
    preflight_steps = build_preflight_steps(
        plan.ops,
        cx.pile_path,
        pile_entries,
    )
    fs_steps = build_fs_mutations(plan)
    manifest_steps = build_manifest_steps(
        cx,
        plan,
        pile_entries,
        verified,
    )
    return ExecutionPlan(preflight_steps, fs_steps, manifest_steps)


def build_checksum_index(ops, pile_root, entries):
    index = manifest.as_manifest_index(entries)
    pairs = [(op.src.relative_to(pile_root), op.src)
             for op in ops if op.action == "copy"]
    return manifest.acquire_verified_checksums(pairs, entries)


def promote_continuity_mappings(
    ops,
    pile_root,
    collection_root,
    filing_root,
):

    mappings = []

    for op in ops:
        if op.action != "copy":
            continue
        src_rel = op.src.relative_to(pile_root)
        subset = manifest.dataset_manifest_subset(op.dataset)
        if subset == "collection":
            dst_rel = op.dst.relative_to(collection_root)
        elif subset == "filing":
            dst_rel = op.dst.relative_to(filing_root)
        else:
            continue
        m = manifest.ContinuityMapping(
            src_subset="pile",
            dst_subset=subset,
            src=src_rel,
            dst=dst_rel,
        )
        mappings.append(m)
    return mappings
