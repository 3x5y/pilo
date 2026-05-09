#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.back import replication as repl


def main():
    cx = context.Context()
    src = cx.root_dataset
    dst = cx.replica_dataset

    status, msg = repl.replication_status(src, dst)

    print(f"STATUS={status.value}")

    if status != repl.ReplicationStatus.OK:
        error.fatal(msg or "replication check failed")


if __name__ == "__main__":
    error.run_main(main)
