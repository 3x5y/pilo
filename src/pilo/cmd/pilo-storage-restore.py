#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.storage import restore


def main():
    cx = context.Context()

    if len(cx.args) < 3:
        error.fatal("usage: restore SRC DST SNAP [--recursive]")

    src, dst, snap, *rest = cx.args
    recursive = "--recursive" in rest

    plan = restore.build_restore_plan(src, dst, snap, recursive)
    restore.execute_restore_plan(plan)


if __name__ == "__main__":
    error.run_main(main)
