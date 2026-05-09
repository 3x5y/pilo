#!/usr/bin/env python3

from pilo import context, error, manifest
from pilo.front import promote


def main():
    cx = context.Context()
    plan = promote.build_promote_plan(cx)
    if not plan:
        return
    promote.execute_promote_plan(cx, plan)

    doms = ["pile", "collection", "filing"]
    plan = manifest.build_manifest_update_plan(cx, doms)
    manifest.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    error.run_main(main)
