#!/usr/bin/env python3

import sys

from pilo import error
from pilo.storage import snapshot


def main():
    if len(sys.argv) < 2:
        error.fatal("require snapshot name")
    snapshot.create_snapshot(sys.argv[1])


if __name__ == "__main__":
    error.run_main(main)
