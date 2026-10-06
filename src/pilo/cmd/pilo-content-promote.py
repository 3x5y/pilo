#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.content import promote
from pilo.content import execution


def main():
    cx = context.Context()
    plan = promote.build_promote_plan(cx)
    if not plan:
        return

    exec_plan = promote.build_exec_plan(cx, plan)
    execution.execute_plan(cx, exec_plan)


if __name__ == "__main__":
    error.run_main(main)
