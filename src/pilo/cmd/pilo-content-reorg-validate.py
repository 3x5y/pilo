#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.content import reorg


def main():
    cx = context.Context()
    script = reorg.load_rewrite_script(cx)
    if not script.lines:
        error.fatal("missing command")

    ops = script.parse_ops()
    reorg.build_rewrite_plan(cx, ops)

    print("valid")


if __name__ == "__main__":
    error.run_main(main)
