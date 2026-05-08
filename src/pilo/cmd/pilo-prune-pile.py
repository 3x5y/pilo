#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()
    plan = pilo.build_prune_plan(
        cx.pile_path,
        cx.pile_dataset,
    )
    pilo.execute_prune_plan(cx, plan)


if __name__ == "__main__":
    pilo.run_main(main)
