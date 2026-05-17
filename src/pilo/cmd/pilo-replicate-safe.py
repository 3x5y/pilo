#!/usr/bin/env python3

import sys

from pilo import context
from pilo import error
from pilo import state
from pilo.back import replication as repl


def main():
    cx = context.Context()

    detected = state.detect_lifecycle(cx)

    if detected.secondary is None:
        error.fatal(detected.message or "no secondary available")

    if detected.state == state.LifecycleState.REPLICATION_DIVERGED:
        error.fatal(detected.message or "replication diverged")

    src = cx.root_dataset
    dst = detected.secondary

    status, msg = repl.replication_status(src, dst)

    if status == repl.ReplicationStatus.OK:
        return

    if status != repl.ReplicationStatus.BEHIND:
        print(f"STATUS={status.value}")
        error.fatal(msg)

    repl.replicate(src, dst)
    status, msg = repl.replication_status(src, dst)

    if status != repl.ReplicationStatus.OK:
        print(f"STATUS={status.value}")
        if msg:
            print(msg)
        error.fatal("replication did not converge")


if __name__ == "__main__":
    error.run_main(main)
