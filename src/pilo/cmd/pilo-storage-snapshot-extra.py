#!/usr/bin/env python3

import os
import sys

from pilo import error
from pilo.storage.snapshot import create_extra_snapshot


def main():
    if len(sys.argv) < 2:
        error.fatal("require snapshot label")
    create_extra_snapshot(os.environ["PILO_PRIMARY_ROOT"],
                          sys.argv[1])


if __name__ == "__main__":
    error.run_main(main)
