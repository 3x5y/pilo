#!/usr/bin/env python3

import os

from pilo import error
from pilo.storage import rollups


def main():
    dataset = os.environ["PILO_PRIMARY_ROOT"]
    plan = rollups.build_rollup_plan(dataset)
    for p in rollups.execute_rollup_plan(plan):
        print(f"ROLLUP {p}")


if __name__ == "__main__":
    error.run_main(main)
