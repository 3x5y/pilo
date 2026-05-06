#!/usr/bin/env python3

import os
import subprocess
import sys

import pilo


def main():
    cx = pilo.Context()
    src = cx.root_dataset
    dst = cx.replica_dataset

    status, msg = pilo.replication_status(src, dst)

    print(f"STATUS={status.value}")

    if status != pilo.ReplicationStatus.OK:
        pilo.fatal(msg or "replication check failed")


if __name__ == "__main__":
    main()
