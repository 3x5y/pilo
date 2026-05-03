#!/usr/bin/env python3

import os
import shutil
import sys

from pilo import fatal, require_dataset, Context


def main():
    cx = Context(os.environ, sys.argv)

    if not cx.args:
        fatal("missing argument: source file")

    src = cx.args[0]

    if not os.path.exists(src):
        fatal(f"source file missing: {src}")

    require_dataset(cx.intake_dataset)
    name = os.path.basename(src)
    dst = os.path.join(cx.intake_path, name)

    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, copy_function=shutil.copy2, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    except Exception as e:
        fatal(str(e))


if __name__ == "__main__":
    main()
