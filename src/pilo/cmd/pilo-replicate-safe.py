#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import state
from pilo.back import continuity
from pilo.back import replication as repl


def main():
    cx = context.Context()

    detected = state.detect_lifecycle(cx)

    if not state.lifecycle_has_secondary(detected):
        error.fatal(detected.message or "no secondary available")

    if not state.lifecycle_replication_permitted(detected):
        error.fatal(
            detected.message or
            "replication not permitted in current lifecycle state"
        )

    src = cx.root_dataset
    dst = detected.secondary

    status, msg = repl.replication_status(src, dst)

    if status == repl.ReplicationStatus.OK:
        return

    if status != repl.ReplicationStatus.BEHIND:
        print(f"STATUS={status.value}")
        error.fatal(msg)

    label = continuity.label_for_secondary(cx, dst)
    plan = repl.build_replication_plan(src, dst, label=label)
    repl.execute_replication_plan(plan)

    status, msg = repl.replication_status(src, dst)

    if status != repl.ReplicationStatus.OK:
        print(f"STATUS={status.value}")
        if msg:
            print(msg)
        error.fatal("replication did not converge")


if __name__ == "__main__":
    error.run_main(main)
