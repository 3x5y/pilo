#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage.cloud import pack_stream_set, find_duplicate_export_membership


def main():
    args = sys.argv[1:]

    if len(args) != 2:
        print("Usage: pilo storage-cloud-pack <stream-root> <cloud-root>",
              file=sys.stderr)
        sys.exit(1)

    stream_root = Path(args[0])
    cloud_root = Path(args[1])

    try:
        archive_path = pack_stream_set(stream_root, cloud_root)
    except ValueError as e:
        error.fatal(str(e))

    dups = find_duplicate_export_membership(cloud_root)
    if dups:
        for path, stamps in sorted(dups.items()):
            print(
                f"WARNING: {path} appears in {len(stamps)} packages: "
                f"{', '.join(stamps)}",
                file=sys.stderr,
            )

    print(archive_path)


if __name__ == "__main__":
    error.run_main(main)
