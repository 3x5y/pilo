#!/usr/bin/env python3

import os
import sys

import pilo


def get_incr_basis(src, dst):
    guid = pilo.get_latest_guid(dst)
    if not guid:
        return None

    for name, g in pilo.zfs_snapshot_guids(src):
        if g == guid:
            return name
    return None


def zfs_replicate(last_src, dst, base=None):
    if base is not None:
        send_opts = ["-I", base]
    else:
        send_opts = []
    send_cmd = ["zfs", "send", "-h", "-R"] + send_opts + [last_src]
    recv_cmd = ["zfs", "receive", "-u", "-o", "readonly=on", dst]
    pilo.simple_pipe(send_cmd, recv_cmd)


def main():

    if len(sys.argv) > 1:
        src = sys.argv[1]
        dst = sys.argv[2]
    else:
        src = os.environ["PILO_ROOT"]
        dst = os.environ["PILO_REPLICA_ROOT"]

    last_src = pilo.zfs_latest_snapshot(src)
    last_dst = pilo.zfs_latest_snapshot(dst)

    if not last_src:
        pilo.fatal("no source snapshot")

    if not last_dst:
        zfs_replicate(last_src, dst)
    else:
        base = get_incr_basis(src, dst)
        if not base:
            pilo.fatal(f"base snapshot missing on source: {base}")
        if last_src == base:
            return # idempotent
        zfs_replicate(last_src, dst, base)


if __name__ == "__main__":
    main()
