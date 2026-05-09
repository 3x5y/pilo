#!/usr/bin/env python3

from pathlib import Path

from pilo import context, error, manifest
from pilo.front import replace


def main():
    cx = context.Context()

    if len(cx.args) < 2:
        error.fatal("missing arguments")

    src = Path(cx.args[0])
    dst_rel = Path(cx.args[1])

    plan = replace.build_replace_plan(cx, src, dst_rel)
    replace.execute_replace_plan(cx, plan)

    plan = manifest.build_manifest_update_plan(cx, ["pile"])
    manifest.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    error.run_main(main)
