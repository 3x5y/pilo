#!/usr/bin/env python3

import os
import sys
import subprocess
import pilo


def latest_snapshot(dataset):
    snaps = pilo.zfs_list_snapshots(dataset)
    return snaps[-1] if snaps else None


def validate_target(target, root):
    if not target.startswith(root):
        pilo.fatal("target outside PILO_ROOT")


def map_to_replica(target, root, repl_root):
    suffix = target[len(root):].lstrip("/")
    return f"{repl_root}/{suffix}" if suffix else repl_root


def main():
    root = os.environ["PILO_ROOT"]
    repl_root = os.environ["PILO_REPLICA_ROOT"]

    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = root

    validate_target(target, root)

    replica = map_to_replica(target, root, repl_root)

    snap = pilo.zfs_latest_snapshot(replica)
    if not snap:
        pilo.fatal("no snapshots on replica")

    if pilo.dataset_exists(target):
        pilo.fatal(f"destination exists: {target}")

    pilo.zfs_send_recv(snap, target, recursive=True)

    subprocess.run(["pilo", "status"], check=False)

if __name__ == "__main__":
    main()
