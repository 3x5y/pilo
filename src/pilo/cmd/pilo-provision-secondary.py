#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.back import provision


def main():
    cx = context.Context()
    if not cx.args:
        error.fatal("missing argument: secondary root dataset")
    provision.provision_secondary(cx.args[0])


if __name__ == "__main__":
    error.run_main(main)

