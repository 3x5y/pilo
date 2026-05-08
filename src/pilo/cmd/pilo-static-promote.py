#!/usr/bin/env python3

from pathlib import Path

import pilo


def main():
    cx = pilo.Context()
    plan = pilo.build_promote_plan(cx)
    if not plan:
        return
    pilo.execute_promote_plan(cx, plan)

    doms = ["pile", "collection", "filing"]
    plan = pilo.build_manifest_update_plan(cx, doms)
    pilo.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    main()
