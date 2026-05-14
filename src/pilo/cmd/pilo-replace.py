#!/usr/bin/env python3

from pathlib import Path

from pilo import context
from pilo import error
from pilo import execution
from pilo.front import replace


def main():
    cx = context.Context()

    if len(cx.args) < 2:
        error.fatal("missing arguments")

    src = Path(cx.args[0])
    dst_rel = Path(cx.args[1])

    plan = replace.build_replace_plan(cx, src, dst_rel)
    exec_plan = replace.build_exec_plan(cx, plan)
    execution.execute_plan(cx, exec_plan)

if __name__ == "__main__":
    error.run_main(main)
