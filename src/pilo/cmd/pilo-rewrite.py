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


def load_rewrite_script(cx):
    lines = load_rewrite_lines(cx)
    return rewrite.RewriteScript.from_lines(lines)


def main():
    cx = context.Context()

    script = load_rewrite_script(cx)
    if not script.lines:
        error.fatal("missing command")

    ops = script.parse_ops()
    plan = rewrite.build_rewrite_plan(cx, ops)
    rewrite.execute_rewrite_plan(cx, plan)

    doms = ["pile", "collection", "filing"]
    plan = manifest.build_manifest_update_plan(cx, doms)
    manifest.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    error.run_main(main)
