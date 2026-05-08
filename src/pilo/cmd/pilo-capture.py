#!/usr/bin/env python3

import shutil
from pathlib import Path

import pilo

def main():
    cx = pilo.Context()

    if not cx.args:
        pilo.fatal("missing argument: source file")

    src = Path(cx.args[0])

    if not src.exists():
        pilo.fatal(f"source file missing: {src}")

    pilo.require_dataset(cx.intake_dataset)

    dst = cx.intake_path / src.name
    if dst.exists():
        pilo.fatal(f"destination already exists: {dst}")

    try:
        if src.is_dir():
            shutil.copytree(src, dst, copy_function=shutil.copy2, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    except Exception as e:
        pilo.fatal(str(e))


if __name__ == "__main__":
    pilo.run_main(main)
