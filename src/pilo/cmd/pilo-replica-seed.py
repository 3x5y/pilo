#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import state
from pilo.back import replication as repl


def main():

    cx = context.Context()

    detected = state.detect_lifecycle(cx)

    if detected.secondary is None:
        error.fatal(detected.message or "no secondary available")

    if detected.state != state.LifecycleState.REPLICA_UNINITIALIZED:
        error.fatal("secondary already initialized")

    repl.execute_replication_plan(
        repl.build_seed_replication_plan(
            cx.root_dataset,
            detected.secondary,
        )
    )


if __name__ == "__main__":
    error.run_main(main)
