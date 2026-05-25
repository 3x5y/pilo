#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage import streams


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: pilo stream-verify <path> [<path> ...]", file=sys.stderr)
        sys.exit(1)

    exit_code = 0
    for arg in args:
        status, msg = streams.verify_one(Path(arg))
        print(f"{status} {msg}")
        if status != "OK":
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    error.run_main(main)
