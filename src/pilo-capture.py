#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys


def fatal(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def dataset_exists(dataset):
    result = subprocess.run(
        ["zfs", "list", dataset],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def require_dataset(dataset):
    if not dataset_exists(dataset):
        fatal(f"missing required dataset: {dataset}")


def main():
    if len(sys.argv) < 2:
        fatal("missing argument: source file")

    src = sys.argv[1]

    intake_dataset = os.environ.get("PILO_INTAKE_DATASET")
    intake_path = os.environ.get("PILO_INTAKE_PATH")

    if not intake_dataset or not intake_path:
        fatal("environment not configured")

    require_dataset(intake_dataset)

    if not os.path.exists(src):
        fatal(f"source file missing: {src}")

    # destination path
    dst = os.path.join(intake_path, os.path.basename(src))

    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, copy_function=shutil.copy2, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    except Exception as e:
        fatal(str(e))


if __name__ == "__main__":
    main()
