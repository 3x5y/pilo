#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage.cloud import (
    find_exported_stream_manifests,
    find_unexported_stream_manifests,
    find_duplicate_export_membership,
    find_unsigned_cloud_manifests,
    iter_cloud_manifests,
    is_authoritative_cloud_manifest,
)


def main():
    args = sys.argv[1:]

    if len(args) < 2 or len(args) > 3:
        print(
            "Usage: pilo storage-cloud-export-audit "
            "<stream-root> <cloud-root> [pubkey]",
            file=sys.stderr,
        )
        sys.exit(1)

    stream_root = Path(args[0])
    cloud_root = Path(args[1])
    pubkey = args[2] if len(args) > 2 else None

    try:
        for mf in find_unsigned_cloud_manifests(cloud_root):
            print(f"UNSIGNED  {mf}")

        for mf in sorted(find_exported_stream_manifests(cloud_root, pubkey)):
            print(f"EXPORTED  {mf}")

        for mf in find_unexported_stream_manifests(stream_root, cloud_root, pubkey):
            print(f"UNEXPORTED  {mf}")

        dups = find_duplicate_export_membership(cloud_root, pubkey)
        for path, stamps in sorted(dups.items()):
            print(f"DUPLICATE  {path}  ({', '.join(stamps)})")

        if pubkey is not None:
            for mf_path, _cm in iter_cloud_manifests(cloud_root):
                if not is_authoritative_cloud_manifest(mf_path, pubkey):
                    print(f"INVALID  {mf_path}")

    except ValueError as e:
        error.fatal(str(e))


if __name__ == "__main__":
    error.run_main(main)
