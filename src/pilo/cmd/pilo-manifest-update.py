#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import manifest_update


def main():
    cx = context.Context()
    doms = ["pile", "collection", "filing"]
    plan = manifest_update.build_manifest_update_plan(cx, doms)
    manifest_update.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    error.run_main(main)
