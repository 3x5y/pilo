#!/usr/bin/env python3

import os
import pilo


def main():
    root = os.environ["PILO_ROOT"]
    ts = pilo.snapshot_timestamp()
    pilo.zfs_snapshot(f"r-{ts}", root)


if __name__ == "__main__":
    main()
