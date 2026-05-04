#!/usr/bin/env python3

import os
import sys
import subprocess

import pilo


def main():
    if len(sys.argv) < 2:
        pilo.fatal("missing anchor type")

    pilo.create_anchor(sys.argv[1])


if __name__ == "__main__":
    main()
