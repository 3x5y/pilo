#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.back import provision


def main():
    cx = context.Context()
    provision.provision_primary(cx)


if __name__ == "__main__":
    error.run_main(main)
