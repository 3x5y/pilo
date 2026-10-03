#!/usr/bin/env python3

from pilo import checks
from pilo import context
from pilo import error
from pilo.storage import normalize


def main():
    cx = context.Context()
    normalize.normalize_system(cx)


if __name__ == "__main__":
    error.run_main(main)
