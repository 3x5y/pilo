#!/usr/bin/env python3

from pathlib import Path

import pilo


def main():
    cx = pilo.Context()

    if len(cx.args) < 2:
        pilo.fatal("missing arguments")

    src = Path(cx.args[0])
    dst_rel = Path(cx.args[1])

    if not src.is_file():
        pilo.fatal(f"source file missing: {src}")

    resolved = cx.resolve(dst_rel)

    if not resolved.path.is_file():
        pilo.fatal(f"target does not exist: {dst_rel}")

    cx.copy_static(src, resolved)
    plan = pilo.build_manifest_update_plan(cx, ["pile"])
    pilo.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    main()
