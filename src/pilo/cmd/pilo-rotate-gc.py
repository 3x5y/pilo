#!/usr/bin/env python3

import os

from pilo import context
from pilo import error
from pilo import state
from pilo.back import continuity


def main():
    cx = context.Context()
    detected = state.detect_lifecycle(cx)

    if state.lifecycle_requires_provisioning(detected):
        error.fatal("secondary requires provisioning")

    if not state.lifecycle_has_secondary(detected):
        error.fatal(detected.message or "no secondary available")

    keep = int(os.environ.get("PILO_ROTATE_GC_KEEP", "1"))

    secondary_root = detected.secondary
    plan = continuity.ageing_plan(cx, secondary_root, keep=keep)
    continuity.execute_ageing_plan(cx, secondary_root, plan)


if __name__ == "__main__":
    error.run_main(main)
