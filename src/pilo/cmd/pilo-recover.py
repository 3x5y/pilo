#!/usr/bin/env python3

import subprocess
import pilo


def main():
    cx = pilo.Context()

    if cx.args:
        target = cx.args[0]
    else:
        target = cx.root_dataset

    plan = pilo.build_recovery_plan(cx, target)
    pilo.execute_recovery_plan(plan, cx)

    subprocess.run(["pilo", "status"], check=False)


if __name__ == "__main__":
    main()
