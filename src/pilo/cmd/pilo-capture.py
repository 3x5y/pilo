#!/usr/bin/env python3

import shutil
from pathlib import Path

from pilo import checks
from pilo import context
from pilo import error
from pilo import manifest


def main():
    cx = context.Context()

    if not cx.args:
        error.fatal("missing argument: source file")

    src = Path(cx.args[0])

    if not src.exists():
        error.fatal(f"source file missing: {src}")

    checks.require_dataset(cx.intake_dataset)

    dst = cx.intake_path / src.name
    if dst.exists():
        error.fatal(f"destination already exists: {dst}")

    try:
        if src.is_dir():
            shutil.copytree(src, dst, copy_function=shutil.copy2, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    except Exception as e:
        error.fatal(str(e))

    manifest.write_manifest(
        cx,
        cx.intake_path,
        cx.intake_path / 'capture.manifest'
    )

if __name__ == "__main__":
    error.run_main(main)
