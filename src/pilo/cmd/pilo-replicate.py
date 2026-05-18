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

        if state.lifecycle_requires_provisioning(detected):
            error.fatal("secondary requires provisioning")

        if not state.lifecycle_has_secondary(detected):
            error.fatal(detected.message or "no secondary available")

        if not state.lifecycle_replication_permitted(detected):
            error.fatal(
                detected.message or
                "replication not permitted in current lifecycle state"
            )

        src = cx.root_dataset
        dst = detected.secondary

    return repl.replicate(src, dst)


if __name__ == "__main__":
    error.run_main(main)
