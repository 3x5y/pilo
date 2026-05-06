#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()

    if not cx.args:
        pilo.fatal("usage: recover-tree TARGET")

    target = cx.args[0]

    plan = pilo.build_recovery_plan(cx, target)
    pilo.execute_recovery_plan(plan, cx)

    print(f"Restored {target}")


if __name__ == "__main__":
    main()
