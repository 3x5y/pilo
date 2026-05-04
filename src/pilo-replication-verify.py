#!/usr/bin/env python3

import os
import subprocess
import sys

import pilo


def main():
    src = os.environ["PILO_ROOT"]
    dst = os.environ["PILO_REPLICA_ROOT"]

    status, msg = pilo.replication_status(src, dst)

    print(f"STATUS={status.value}")

    if status != pilo.ReplicationStatus.OK:
        pilo.fatal(msg or "replication check failed")


if __name__ == "__main__":
    main()
