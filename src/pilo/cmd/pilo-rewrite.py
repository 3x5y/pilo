#!/usr/bin/env python3

from pathlib import Path
import sys

from pilo import context
from pilo import error
from pilo import manifest
from pilo.front import rewrite


def load_rewrite_lines(cx):
    if cx.args:
        arg = cx.args[0]
        path = Path(arg)
        if path.is_file():
            return path.read_text().splitlines()
        return arg.splitlines()
    return sys.stdin.read().splitlines()


def main():
    cx = context.Context()

    lines = load_rewrite_lines(cx)
    if not lines:
        error.fatal("missing command")

    ops = rewrite.parse_rewrite_ops(lines)
    plan = rewrite.build_rewrite_plan(cx, ops)
    rewrite.execute_rewrite_plan(cx, plan)

    doms = ["pile", "collection", "filing"]
    plan = manifest.build_manifest_update_plan(cx, doms)
    manifest.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    error.run_main(main)
