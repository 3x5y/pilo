#!/usr/bin/env python3

import os
import subprocess
import sys

import pilo


def get_incr_basis(src, dst):
    guid = pilo.get_latest_guid(dst)
    if not guid:
        return None

    for name, g in pilo.zfs_list_snapshots_with_guid(src):
        if g == guid:
            return name
    return None


def repl_full(last_src, dst):
    send = subprocess.Popen(
        ["zfs", "send", "-R", last_src],
        stdout=subprocess.PIPE,
    )
    recv = subprocess.Popen(
        ["zfs", "receive", "-h", "-u", "-o", "readonly=on", dst],
        stdin=send.stdout,
    )
    send.stdout.close()
    recv.communicate()

    if send.wait() != 0 or recv.returncode != 0:
        pilo.fatal("replication failed")


def repl_incr(last_src, dst, base):
    send = subprocess.Popen(
        ["zfs", "send", "-h", "-R", "-I", base, last_src],
        stdout=subprocess.PIPE,
    )
    recv = subprocess.Popen(
        ["zfs", "receive", "-u", "-o", "readonly=on", dst],
        stdin=send.stdout,
    )
    send.stdout.close()
    recv.communicate()

    if send.wait() != 0 or recv.returncode != 0:
        pilo.fatal("replication failed")


def main():

    if len(sys.argv) > 1:
        src = sys.argv[1]
        dst = sys.argv[2]
    else:
        src = os.environ["PILO_ROOT"]
        dst = os.environ["PILO_REPLICA_ROOT"]

    src_snaps = pilo.zfs_list_snapshots(src)
    if not src_snaps:
        pilo.fatal("no source snapshot")

    last_src = src_snaps[-1]

    try:
        dst_snaps = pilo.zfs_list_snapshots(dst)
        last_dst = dst_snaps[-1] if dst_snaps else None
    except subprocess.CalledProcessError:
        last_dst = None

    if not last_dst:
        repl_full(last_src, dst)
    else:
        base = get_incr_basis(src, dst)
        if not base:
            pilo.fatal(f"base snapshot missing on source: {base}")
        if last_src == base:
            return # idempotent
        repl_incr(last_src, dst, base)


if __name__ == "__main__":
    main()
