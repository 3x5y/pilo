#!/usr/bin/env python3

import os
import sys

import pilo


def main():
    src = os.environ["PILO_ROOT"]
    dst = os.environ["PILO_REPLICA_ROOT"]

    status, msg = pilo.replication_status(src, dst)

    if status == pilo.ReplicationStatus.OK:
        return

    if status in (pilo.ReplicationStatus.EMPTY, pilo.ReplicationStatus.BEHIND):
        pilo.replicate(src, dst)
    else:
        if msg:
            print(msg)
        sys.exit(1)

    # post-check
    status, msg = pilo.replication_status(src, dst)
    if status != pilo.ReplicationStatus.OK:
        print(f"STATUS={status.value}")
        if msg:
            print(msg)
        pilo.fatal("replication did not converge")


if __name__ == "__main__":
    main()
