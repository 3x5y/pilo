#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

import pilo as P

def run(cmd, **kwargs):
    result = subprocess.run(cmd, text=True, capture_output=True, **kwargs)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout


def main():

    pile_dataset = os.environ["PILO_PILE_DATASET"]
    static_dataset = os.environ["PILO_STATIC_DATASET"]
    static_path = os.environ["PILO_STATIC_PATH"]
    out_path = os.path.join(os.environ["PILO_PILE_PATH"], "out")
    user = os.environ['PILO_USER']

    if not os.path.isdir(out_path):
        return

    def validate_file(src, target, rel):
        dataset = f"{static_dataset}/{target}"
        dst = os.path.join(static_path, target, rel)
        P.require_dataset(dataset)
        if os.path.isfile(dst):
            if not P.files_equal(src, dst):
                P.fatal(f"destination conflict for {rel}")

    def apply_file(src, target, rel):
        dataset = f"{static_dataset}/{target}"
        dst = os.path.join(static_path, target, rel)
        dst_dir = os.path.dirname(dst)

        if not os.path.isfile(dst):
            with P.dataset_writable(dataset):
                P.as_user(["mkdir", "-p", dst_dir])
                #P.as_user(['cp', '-a', src, dst])
                shutil.copy2(src, dst) # doesn't preserve owner
                shutil.chown(dst, user, user)

        with P.dataset_writable(pile_dataset):
            os.remove(src)


    # validate top-level dirs
    for name in os.listdir(out_path):
        full = os.path.join(out_path, name)
        if not os.path.exists(full):
            continue
        if name not in ("collection", "filing"):
            P.fatal(f"invalid /out/ structure: {name}")

    # collect files
    collection_dir = os.path.join(out_path, "collection")
    filing_dir = os.path.join(out_path, "filing")

    col_files = P.files_under(collection_dir) if os.path.isdir(collection_dir) else []
    fil_files = P.files_under(filing_dir) if os.path.isdir(filing_dir) else []

    if not col_files and not fil_files:
        P.fatal("/out/ directory empty")

    # --- validation phase ---

    for f in col_files:
        rel = os.path.relpath(f, collection_dir)
        validate_file(f, "collection", rel)

    for f in fil_files:
        rel = os.path.relpath(f, filing_dir)
        parts = rel.split("/", 1)
        if len(parts) != 2:
            P.fatal("invalid filing structure")

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
