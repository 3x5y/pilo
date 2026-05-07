#!/usr/bin/env python3

import os
from pathlib import Path

import pilo


def main():
    cx = pilo.Context()
    out_path = cx.pile_path / "out"

    if not out_path.is_dir():
        return

    def validate_file(src: Path, rel: Path):
        r = cx.resolve(rel)
        pilo.require_dataset(r.dataset)
        if r.path.is_file():
            if not pilo.files_equal(src, r.path):
                pilo.fatal(f"destination conflict for {rel}")

    def apply_file(src: Path, rel: Path):
        r = cx.resolve(rel)
        if not r.path.is_file():
            cx.copy_static(src, r)
        cx.remove_piled(src)

    # validate top-level dirs
    for child in out_path.iterdir():
        if child.name not in ("collection", "filing"):
            pilo.fatal(f"invalid /out/ structure: {name}")

    # collect files
    col_dir = out_path / "collection"
    fil_dir = out_path / "filing"
    col_files = sorted(pilo.iter_files(col_dir)) if col_dir.is_dir() else []
    fil_files = sorted(pilo.iter_files(fil_dir)) if fil_dir.is_dir() else []
    if not col_files and not fil_files:
        pilo.fatal("/out/ directory empty")

    ops = []

    for f in col_files:
        rel = Path("collection") / f.relative_to(col_dir)
        ops.append((f, rel))

    for f in fil_files:
        rel = f.relative_to(fil_dir)
        if len(rel.parts) < 2:
            pilo.fatal("invalid filing structure")
        subset = rel.parts[0]
        subpath = Path(*rel.parts[1:])
        full_rel = Path("filing") / subset / subpath
        ops.append((f, full_rel))

    for src, rel in ops:
        validate_file(src, rel)

    for src, rel in ops:
        apply_file(src, rel)

    doms = ["pile", "collection", "filing"]
    plan = pilo.build_manifest_update_plan(cx, doms)
    pilo.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    main()
