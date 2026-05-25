#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.storage import replication as repl


def main():
    cx = context.Context()
    plan = repl.build_replica_seed_plan(cx)
    repl.execute_replication_plan(plan)


if __name__ == "__main__":
    error.run_main(main)
