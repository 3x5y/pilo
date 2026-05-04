#!/usr/bin/env python3

import sys
import subprocess
import pilo


def main():
    if len(sys.argv) < 4:
        pilo.fatal("usage: recover-baseline SRC DST SNAP")

    src, dst, snap = sys.argv[1:4]
    src_snap = f"{src}@{snap}"

    # validate snapshot exists
    if subprocess.run(
        ["zfs", "list", "-t", "snapshot", src_snap],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        pilo.fatal(f"source snapshot does not exist: {src_snap}")

    # ensure parent exists
    pilo.zfs_create_parent(dst)

    # destroy destination
    #pilo.zfs_destroy(dst)

    # replicate
    pilo.zfs_send_recv(src_snap, dst)

    # verify
    if subprocess.run(
        ["zfs", "list", "-t", "snapshot", f"{dst}@{snap}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode != 0:
        pilo.fatal("recovery completed but snapshot missing at destination")

    print(f"Recovered {dst} from {src_snap}")


if __name__ == "__main__":
    main()
