#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import state
from pilo.back import continuity
from pilo.back import replication as repl


def main():

    cx = context.Context()
    if len(cx.args) == 2:
        src, dst = cx.args
        return repl.replicate(src, dst)

    detected = state.detect_lifecycle(cx)

    if state.lifecycle_requires_provisioning(detected):
        error.fatal("secondary requires provisioning")

    if not state.lifecycle_has_secondary(detected):
        error.fatal(detected.message or "no secondary available")

    if not state.lifecycle_replication_permitted(detected):
        error.fatal(
            detected.message or
            "replication not permitted in current lifecycle state"
        )

    src = cx.root_dataset
    dst = detected.secondary
    label = continuity.label_for_secondary(cx, dst)

    plan = repl.build_replication_plan(src, dst, label=label)
    return repl.execute_replication_plan(plan)


if __name__ == "__main__":
    error.run_main(main)
