#!/usr/bin/env python3

import sys

from pilo import context
from pilo import error
from pilo.back import replication as repl


def main():
    cx = context.Context()
    src = cx.root_dataset
    dst = cx.replica_dataset

    status, msg = repl.replication_status(src, dst)

    if status == repl.ReplicationStatus.OK:
        return

    if status in (repl.ReplicationStatus.EMPTY, repl.ReplicationStatus.BEHIND):
        repl.replicate(src, dst)
    else:
        if msg:
            print(msg)
        sys.exit(1)

    # post-check
    status, msg = repl.replication_status(src, dst)
    if status != repl.ReplicationStatus.OK:
        print(f"STATUS={status.value}")
        if msg:
            print(msg)
        error.fatal("replication did not converge")


if __name__ == "__main__":
    error.run_main(main)
