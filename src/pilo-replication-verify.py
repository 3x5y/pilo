#!/usr/bin/env python3

import os
import subprocess
import sys

import pilo


def status_ok():
    print("STATUS=OK")
    sys.exit(0)


def status_fail(status, msg):
    print(f"STATUS={status}")
    pilo.fatal(msg)


def zfs_list_filesystems(root):
    result = subprocess.run(
        ["zfs", "list", "-r", "-t", "filesystem", "-Ho", "name", root],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def zfs_list_guids(dataset):
    result = subprocess.run(
        ["zfs", "list", "-t", "snapshot", "-Ho", "guid", dataset],
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(result.stdout.splitlines())


def map_dataset(name, src_root, dst_root):
    suffix = name[len(src_root):].lstrip("/")
    return f"{dst_root}/{suffix}" if suffix else dst_root


def main():
    src = os.environ.get("PILO_ROOT")
    dst = os.environ.get("PILO_REPLICA_ROOT")

    if not src or not dst:
        pilo.fatal("missing replication environment")

    src_guid = pilo.get_latest_guid(src)
    dst_guid = pilo.get_latest_guid(dst)

    if not dst_guid:
        status_fail("EMPTY", "no snapshots on target")

    # --- check target datasets ---
    for dst_ds in zfs_list_filesystems(dst):
        src_ds = map_dataset(dst_ds, dst, src)

        src_guids = set(zfs_list_guids(src_ds))
        dst_guids = set(zfs_list_guids(dst_ds))

        # divergence
        if dst_guids - src_guids:
            status_fail("DIVERGED", f"replication divergence in {dst_ds}")

        src_latest = pilo.get_latest_guid(src_ds)
        dst_latest = pilo.get_latest_guid(dst_ds)

        if dst_latest and src_latest != dst_latest:
            status_fail("BEHIND", f"replication behind in {dst_ds}")

    # --- check missing datasets ---
    for src_ds in zfs_list_filesystems(src):
        dst_ds = map_dataset(src_ds, src, dst)
        result = subprocess.run(
            ["zfs", "list", dst_ds],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            status_fail("BEHIND", f"replication behind, missing {dst_ds}")

    if src_guid != dst_guid:
        status_fail("UNKNOWN", f"GUID mismatch {src} != {dst}")

    status_ok()


if __name__ == "__main__":
    main()
