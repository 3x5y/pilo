#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage.cloud import unpack_archive


def main():
    args = sys.argv[1:]

    if len(args) != 3:
        print(
            "Usage: pilo storage-cloud-unpack "
            "<archive.tar.zst> <destination-root> <cloud-manifest>",
            file=sys.stderr,
        )
        sys.exit(1)

    archive_path = Path(args[0])
    dst_root = Path(args[1])
    manifest_path = Path(args[2])

    dst_path = unpack_archive(archive_path, dst_root, manifest_path)
    print(dst_path)


if __name__ == "__main__":
    error.run_main(main)
