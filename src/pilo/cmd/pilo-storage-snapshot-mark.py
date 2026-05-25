#!/usr/bin/env python3

import os

from pilo import error
from pilo.storage.snapshot import create_mark_snapshot


def main():
    create_mark_snapshot(os.environ["PILO_PRIMARY_ROOT"])


if __name__ == "__main__":
    error.run_main(main)
