#!/usr/bin/env python3

import sys

from pilo import error
from pilo.back import snapshot


def main():
    if len(sys.argv) < 2:
        error.fatal("missing anchor type")

    snapshot.create_anchor(sys.argv[1])


if __name__ == "__main__":
    error.run_main(main)
