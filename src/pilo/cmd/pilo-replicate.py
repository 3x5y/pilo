#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.back import replication as repl


def main():

    cx = context.Context()
    if cx.args:
        src, dst = cx.args
    else:
        src = cx.root_dataset
        dst = cx.current_secondary_dataset
        if not dst:
            error.fatal("no secondary dataset available")

    return repl.replicate(src, dst)


if __name__ == "__main__":
    error.run_main(main)
