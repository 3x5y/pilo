#!/usr/bin/env python3

import os
import sys
import subprocess

import pilo


def main():
    if len(sys.argv) < 2:
        pilo.fatal("missing anchor type")

    anchor_type = sys.argv[1]
    src = os.environ["PILO_ROOT"]

    ts = pilo.snapshot_timestamp()

    if anchor_type == "daily":
        name = f"daily-{ts}"
        hold = False
    elif anchor_type == "rotation":
        name = f"rotation-{ts}"
        hold = True
    else:
        pilo.fatal("invalid anchor type")

    pilo.zfs_snapshot(name, src)

    if hold:
        subprocess.run(
            ["zfs", "hold", "-r", "repl-anchor", f"{src}@{name}"],
            check=True,
        )


if __name__ == "__main__":
    main()
