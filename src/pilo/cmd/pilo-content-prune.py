#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo.content import prune


def main():
    cx = context.Context()
    plan = prune.build_prune_plan(cx.pile_path, cx.pile_dataset)
    prune.execute_prune_plan(cx, plan)


if __name__ == "__main__":
    error.run_main(main)
