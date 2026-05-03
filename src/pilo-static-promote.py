#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

import pilo

def run(cmd, **kwargs):
    result = subprocess.run(cmd, text=True, capture_output=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def main():
    cx = pilo.Context(os.environ)
    out_path = os.path.join(cx.pile_path, "out")

    if not os.path.isdir(out_path):
        return

    def validate_file(src, target, rel):
        dataset = f"{cx.static_dataset}/{target}"
        dst = os.path.join(cx.static_path, target, rel)
        pilo.require_dataset(dataset)
        if os.path.isfile(dst):
            if not pilo.files_equal(src, dst):
                pilo.fatal(f"destination conflict for {rel}")

    def apply_file(src, target, rel):
        dataset = f"{cx.static_dataset}/{target}"
        dst = os.path.join(cx.static_path, target, rel)
        dst_dir = os.path.dirname(dst)

        if not os.path.isfile(dst):
            with pilo.dataset_writable(dataset):
                pilo.as_user(["mkdir", "-p", dst_dir])
                shutil.copy2(src, dst) # doesn't preserve owner
                shutil.chown(dst, cx.user, cx.user)

        with pilo.dataset_writable(cx.pile_dataset):
            os.remove(src)


    # validate top-level dirs
    for name in os.listdir(out_path):
        full = os.path.join(out_path, name)
        if not os.path.exists(full):
            continue
        if name not in ("collection", "filing"):
            pilo.fatal(f"invalid /out/ structure: {name}")

    # collect files
    collection_dir = os.path.join(out_path, "collection")
    filing_dir = os.path.join(out_path, "filing")

    col_files = pilo.files_under(collection_dir) if os.path.isdir(collection_dir) else []
    fil_files = pilo.files_under(filing_dir) if os.path.isdir(filing_dir) else []

    if not col_files and not fil_files:
        pilo.fatal("/out/ directory empty")

    # --- validation phase ---

    for f in col_files:
        rel = os.path.relpath(f, collection_dir)
        validate_file(f, "collection", rel)

    for f in fil_files:
        rel = os.path.relpath(f, filing_dir)
        parts = rel.split("/", 1)
        if len(parts) != 2:
            pilo.fatal("invalid filing structure")

        dataset, subpath = parts
        validate_file(f, f"filing/{dataset}", subpath)

    # --- apply phase ---

    for f in col_files:
        rel = os.path.relpath(f, collection_dir)
        apply_file(f, "collection", rel)

    for f in fil_files:
        rel = os.path.relpath(f, filing_dir)
        dataset, subpath = rel.split("/", 1)
        apply_file(f, f"filing/{dataset}", subpath)

    # update manifests
    subprocess.run(["pilo", "manifest-update"], check=True)


if __name__ == "__main__":
    main()
