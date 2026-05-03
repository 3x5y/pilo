#!/usr/bin/env python3

import os
import shutil
import sys

from pilo import fatal, require_env, require_dataset


def main():
    if len(sys.argv) < 2:
        fatal("missing argument: source file")

    src = sys.argv[1]
    if not os.path.exists(src):
        fatal(f"source file missing: {src}")

    intake_dataset = require_env("PILO_INTAKE_DATASET")
    intake_path = require_env("PILO_INTAKE_PATH")
    require_dataset(intake_dataset)
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
