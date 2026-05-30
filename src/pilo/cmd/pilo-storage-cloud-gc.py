#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage.cloud import (
    build_cloud_gc_plan,
    describe_cloud_gc_state,
    execute_cloud_gc_plan,
)


def _stamp_from_manifest(name: str) -> str:
    for suffix in (".tar.zst.age.manifest", ".tar.zst.manifest"):
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return name


def main():
    args = sys.argv[1:]

    preview = "--preview" in args
    if preview:
        args = [a for a in args if a != "--preview"]

    if len(args) != 3:
        print(
            "Usage: pilo storage-cloud-gc "
            "<stream-root> <cloud-root> <pubkey> [--preview]",
            file=sys.stderr,
        )
        sys.exit(1)

    stream_root = Path(args[0])
    cloud_root = Path(args[1])
    pubkey = args[2]

    try:
        if preview:
            statuses = describe_cloud_gc_state(stream_root, cloud_root, pubkey)
            statuses.sort(key=lambda s: _stamp_from_manifest(s.manifest_path.name))
            for st in statuses:
                stamp = _stamp_from_manifest(st.manifest_path.name)
                if st.removable:
                    print(f"REMOVE {stamp} live={st.live_refs} dead={st.dead_refs}")
                else:
                    print(f"KEEP   {stamp} live={st.live_refs} dead={st.dead_refs}")
        else:
            plan = build_cloud_gc_plan(stream_root, cloud_root, pubkey)
            if not plan:
                print("nothing to remove", file=sys.stderr)
                return
            results = execute_cloud_gc_plan(plan)
            for r in results:
                print(f"REMOVED {r.stamp}")
    except ValueError as e:
        error.fatal(str(e))


if __name__ == "__main__":
    error.run_main(main)
