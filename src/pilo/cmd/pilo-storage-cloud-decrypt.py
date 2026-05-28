#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage.cloud import decrypt_archive


def main():
    args = sys.argv[1:]

    if len(args) != 3:
        print(
            "Usage: pilo storage-cloud-decrypt "
            "<identity-key> <archive.tar.zst.age> <output-dir>",
            file=sys.stderr,
        )
        sys.exit(1)

    identity = Path(args[0])
    archive_path = Path(args[1])
    dst_dir = Path(args[2])

    try:
        output_path = decrypt_archive(archive_path, dst_dir, identity)
    except ValueError as e:
        error.fatal(str(e))

    print(output_path)


if __name__ == "__main__":
    error.run_main(main)
