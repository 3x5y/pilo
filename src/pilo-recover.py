#!/usr/bin/env python3

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
    cx = pilo.Context()
    root = cx.root_dataset
    repl_root = cx.replica_dataset

    if cx.args:
        target = cx.args[0]
    else:
        target = root

    validate_target(target, root)

    replica = map_to_replica(target, root, repl_root)

    pilo.recover_dataset_tree(cx, target, replica)

    subprocess.run(["pilo", "status"], check=False)


if __name__ == "__main__":
    main()
