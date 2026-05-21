#!/usr/bin/env python3

import os

from pilo import context
from pilo import error
from pilo import lifecycle
from pilo.back import continuity


def main():
    cx = context.Context()
    detected = lifecycle.detect_lifecycle(cx)

    if lifecycle.lifecycle_requires_provisioning(detected):
        error.fatal("secondary requires provisioning")

    if not lifecycle.lifecycle_has_secondary(detected):
        error.fatal(detected.message or "no secondary available")

    keep = int(os.environ.get("PILO_ROTATE_GC_KEEP", "1"))

    secondary_root = detected.secondary
    plan = continuity.ageing_plan(cx, secondary_root, keep=keep)

    if continuity.is_preview_mode(cx):
        for line in continuity.preview_ageing_plan(plan):
            print(line)
        return

    continuity.execute_ageing_plan(cx, secondary_root, plan)


if __name__ == "__main__":
    error.run_main(main)
