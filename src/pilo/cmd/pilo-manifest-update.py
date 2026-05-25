#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.content import manifest


def main():
    cx = context.Context()
    doms = ["pile", "collection", "filing"]
    plan = manifest.build_manifest_update_plan(cx, doms)
    manifest.execute_manifest_update_plan(cx, plan)


if __name__ == "__main__":
    error.run_main(main)
