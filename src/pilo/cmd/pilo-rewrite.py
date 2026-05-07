#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()
    if len(cx.args) < 1:
        pilo.fatal("missing command")
    cmd = cx.args[0].splitlines()
    ops = pilo.parse_rewrite_ops(cmd)
    plan = pilo.build_rewrite_plan(cx, ops)
    pilo.execute_rewrite_plan(cx, plan)
    doms = ["pile", "collection", "filing"]
    plan = pilo.build_manifest_update_plan(cx, doms)
    pilo.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    main()
