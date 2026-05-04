#!/usr/bin/env python3

import os
import sys
import pilo


def main():
    if len(sys.argv) < 2:
        pilo.fatal("require snapshot name")

    name = sys.argv[1]
    root = os.environ["PILO_ROOT"]

    pilo.zfs_snapshot(name, root)


if __name__ == "__main__":
    main()
