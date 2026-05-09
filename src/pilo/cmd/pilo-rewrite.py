#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import manifest
from pilo.front import rewrite


def main():
    cx = context.Context()
    if len(cx.args) < 1:
        error.fatal("missing command")
    cmd = cx.args[0].splitlines()
    ops = rewrite.parse_rewrite_ops(cmd)
    plan = rewrite.build_rewrite_plan(cx, ops)
    rewrite.execute_rewrite_plan(cx, plan)
    doms = ["pile", "collection", "filing"]
    plan = manifest.build_manifest_update_plan(cx, doms)
    manifest.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    error.run_main(main)
