#!/usr/bin/env python3

from pilo import error
from pilo.back import snapshot


def main():
    snapshot.create_prefixed_snapshot("r")


if __name__ == "__main__":
    error.run_main(main)
