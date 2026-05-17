#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import state
from pilo.back import replication as repl


def main():

    cx = context.Context()
    if cx.args:
        src, dst = cx.args
    else:
        detected = state.detect_lifecycle(cx)
        if detected.state == state.LifecycleState.REPLICA_UNINITIALIZED:
            error.fatal("secondary requires provisioning")
        if detected.secondary is None:
            error.fatal(detected.message or "no secondary available")

        src = cx.root_dataset
        dst = detected.secondary

    return repl.replicate(src, dst)


if __name__ == "__main__":
    error.run_main(main)
