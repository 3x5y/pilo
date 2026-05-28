#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage.cloud import verify_cloud_manifest


def main():
    args = sys.argv[1:]

    if len(args) != 2:
        print(
            "Usage: pilo storage-cloud-verify-manifest "
            "<pubkey> <manifest>",
            file=sys.stderr,
        )
        sys.exit(1)

    pubkey = args[0]
    manifest_path = Path(args[1])

    try:
        archive_path = verify_cloud_manifest(manifest_path, pubkey)
    except ValueError as e:
        error.fatal(str(e))

    print(archive_path)


if __name__ == "__main__":
    error.run_main(main)
