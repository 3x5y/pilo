#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()

    if len(cx.args) < 3:
        pilo.fatal("usage: restore SRC DST SNAP [--recursive]")

    src, dst, snap, *rest = cx.args
    recursive = "--recursive" in rest

    plan = pilo.build_restore_plan(src, dst, snap, recursive)
    pilo.execute_restore_plan(plan)


if __name__ == "__main__":
    pilo.run_main(main)
