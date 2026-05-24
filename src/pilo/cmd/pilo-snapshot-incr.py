#!/usr/bin/env python3

import os

from pilo import error
from pilo.back.snapshot import create_incremental_snapshot


def main():
    create_incremental_snapshot(os.environ["PILO_PRIMARY_ROOT"])


if __name__ == "__main__":
    error.run_main(main)
