#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.front import rewrite


def main():
    cx = context.Context()
    script = rewrite.load_rewrite_script(cx)
    if not script.lines:
        error.fatal("missing command")

    ops = script.parse_ops()
    rewrite.build_rewrite_plan(cx, ops)

    print("valid")


if __name__ == "__main__":
    error.run_main(main)
