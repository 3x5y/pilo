#!/usr/bin/env python3

import os
import subprocess
import shutil
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
            with pilo.dataset_writable(r.dataset):
                cx.copy(src, r.path)
        with pilo.dataset_writable(cx.pile_dataset):
            src.unlink()

    # validate top-level dirs
    for child in out_path.iterdir():
        if not child.exists():
            continue
        if child.name not in ("collection", "filing"):
            pilo.fatal(f"invalid /out/ structure: {name}")

    # collect files
    col_dir = out_path / "collection"
    fil_dir = out_path / "filing"
    col_files = sorted(pilo.iter_files(col_dir)) if col_dir.is_dir() else []
    fil_files = sorted(pilo.iter_files(fil_dir)) if fil_dir.is_dir() else []
    if not col_files and not fil_files:
        pilo.fatal("/out/ directory empty")

    # --- validation phase ---

    for f in col_files:
        rel = Path("collection") / f.relative_to(col_dir)
        validate_file(f, rel)

    for f in fil_files:
        rel = f.relative_to(fil_dir)
        if len(rel.parts) < 2:
            pilo.fatal("invalid filing structure")
        subset = rel.parts[0]
        subpath = Path(*rel.parts[1:])
        full_rel = Path("filing") / subset / subpath
        validate_file(f, full_rel)

    # --- apply phase ---

    for f in col_files:
        rel = Path("collection") / f.relative_to(col_dir)
        apply_file(f, rel)

    for f in fil_files:
        rel = f.relative_to(fil_dir)
        subset = rel.parts[0]
        subpath = Path(*rel.parts[1:])
        full_rel = Path("filing") / subset / subpath
        apply_file(f, full_rel)

    # update manifests
    subprocess.run(["pilo", "manifest-update"], check=True)


if __name__ == "__main__":
    main()
