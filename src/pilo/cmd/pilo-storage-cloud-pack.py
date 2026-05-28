#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage.cloud import pack_stream_day


def main():
    args = sys.argv[1:]

    if len(args) != 2:
        print("Usage: pilo storage-cloud-pack <YYYYMMDD-dir> <output-dir>",
              file=sys.stderr)
        sys.exit(1)

    src_dir = Path(args[0])
    dst_dir = Path(args[1])

    try:
        archive_path = pack_stream_day(src_dir, dst_dir)
    except ValueError as e:
        error.fatal(str(e))

    print(archive_path)


if __name__ == "__main__":
    error.run_main(main)
