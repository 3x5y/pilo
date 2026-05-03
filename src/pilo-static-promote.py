#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from pathlib import Path

import pilo


def main():
    cx = pilo.Context(os.environ)
    out_path = cx.pile_path / "out"

    if not out_path.is_dir():
        return

    def dataset_for(target):
        return f"{cx.static_dataset}/{target}"

    def validate_file(src, target, rel):
        static_dataset = dataset_for(target)
        pilo.require_dataset(static_dataset)
        dst = cx.static_path / target / rel
        if dst.is_file():
            if not pilo.files_equal(src, dst):
                pilo.fatal(f"destination conflict for {rel}")

    def apply_file(src, target, rel):
        static_dataset = dataset_for(target)
        dst = cx.static_path / target / rel
        dst_dir = dst.parent
        if not dst.is_file():
            with pilo.dataset_writable(static_dataset):
                cx.copy(src, dst)
        with pilo.dataset_writable(cx.pile_dataset):
            os.remove(src)

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
        rel = f.relative_to(col_dir)
        validate_file(f, "collection", rel)

    for f in fil_files:
        rel = f.relative_to(fil_dir)
        if len(rel.parts) < 2:
            pilo.fatal("invalid filing structure")

        subset = rel.parts[0]
        subpath = Path(*rel.parts[1:])
        validate_file(f, f"filing/{subset}", subpath)

    # --- apply phase ---

    for f in col_files:
        rel = f.relative_to(col_dir)
        apply_file(f, "collection", rel)

    for f in fil_files:
        rel = f.relative_to(fil_dir)
        subset = rel.parts[0]
        subpath = Path(*rel.parts[1:])
        apply_file(f, f"filing/{subset}", subpath)

    # update manifests
    subprocess.run(["pilo", "manifest-update"], check=True)


if __name__ == "__main__":
    main()
