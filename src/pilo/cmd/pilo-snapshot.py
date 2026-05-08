#!/usr/bin/env python3

import sys
import pilo


def main():
    if len(sys.argv) < 2:
        pilo.fatal("require snapshot name")
    pilo.create_snapshot(sys.argv[1])


if __name__ == "__main__":
    pilo.run_main(main)
