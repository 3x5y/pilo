#!/usr/bin/env python3

import os
import sys

import pilo


def main():

    if len(sys.argv) > 1:
        src = sys.argv[1]
        dst = sys.argv[2]
    else:
        src = os.environ["PILO_ROOT"]
        dst = os.environ["PILO_REPLICA_ROOT"]

    return pilo.replicate(src, dst)


if __name__ == "__main__":
    main()
