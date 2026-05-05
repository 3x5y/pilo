#!/usr/bin/env python3

import os
from pathlib import Path

import pilo


def check_transient(cx, st: pilo.Status):
    for git_dir in cx.admin_path.rglob(".git"):
        repo = git_dir.parent
        if pilo.git_dirty(repo):
            st.warn(f"transient: repo {repo} has uncommitted changes")


def check_pile(cx, st: pilo.Status):
    pile = cx.pile_path
    if not pile.exists():
        return

    now = pilo.now_epoch()
    max_age = int(os.environ.get("CONFIG_PILE_MAX_AGE", "86400"))

    for f in pilo.iter_files(pile):
        age = now - int(f.stat().st_mtime)
        if age > max_age:
            st.warn(f"pile: {f} is older than threshold")


def check_snapshot(cx, st: pilo.Status):
    dataset = cx.pile_dataset

    name, ts = pilo.zfs_latest_snapshot_with_time(dataset)

    if not name:
        st.warn(f"snapshot: none for {dataset}")
        return

    now = pilo.now_epoch()
    max_age = int(os.environ.get("CONFIG_SNAPSHOT_MAX_AGE", "3600"))

    if ts is None:
        st.warn("snapshot: could not parse timestamp")
        return

    age = now - ts

    if age > max_age:
        st.warn(f"snapshot: stale ({age} s)")
    else:
        st.ok(f"snapshot: fresh ({age} s)")


def check_replication(cx, st: pilo.Status):
    src = cx.root_dataset
    dst = cx.replica_dataset

    src_snap = pilo.zfs_latest_snapshot(src)
    dst_snap = pilo.zfs_latest_snapshot(dst)

    src_name = src_snap.split("@", 1)[1] if src_snap else "**MISSING**"
    dst_name = dst_snap.split("@", 1)[1] if dst_snap else "**MISSING**"

    if src_name != dst_name:
        st.warn(f"replication: latest={src_name} replicated={dst_name}")
    else:
        st.ok(f"replication: {src_name}")


def check_datasets(cx, st: pilo.Status):
    required = [
        cx.admin_dataset,
        cx.intake_dataset,
        cx.pile_dataset,
        f"{cx.static_dataset}/collection",
    ]

    for ds in required:
        if not pilo.dataset_exists(ds):
            st.warn(f"incomplete: missing dataset {ds}")


def main():
    cx = pilo.Context()
    st = pilo.Status()

    check = cx.args[0] if cx.args else None

    checks = {
        "transient": check_transient,
        "pile": check_pile,
        "snapshot": check_snapshot,
        "replication": check_replication,
        "datasets": check_datasets,
    }

    for name, fn in checks.items():
        if check is None or check == name:
            fn(cx, st)

    exit(st.code)


if __name__ == "__main__":
    main()
