#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import state
from pilo.back import replication as repl


def main():
    cx = context.Context()

    detected = state.detect_lifecycle(cx)

    if detected.secondary is None:
        error.fatal(detected.message or "no secondary available")

    src = cx.root_dataset
    dst = detected.secondary

    status, msg = repl.replication_status(src, dst)

    print(f"STATUS={status.value}")

    if status != repl.ReplicationStatus.OK:
        error.fatal(msg or "replication check failed")


if __name__ == "__main__":
    error.run_main(main)
