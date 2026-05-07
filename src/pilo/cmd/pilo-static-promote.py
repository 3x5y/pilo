#!/usr/bin/env python3

from pathlib import Path

import pilo


def main():
    cx = pilo.Context()
    ops = pilo.build_promote_plan(cx)
    if not ops:
        return
    pilo.execute_promote_plan(cx, ops)

    doms = ["pile", "collection", "filing"]
    plan = pilo.build_manifest_update_plan(cx, doms)
    pilo.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    main()
