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

    st = pilo.collect_system_status(cx)
    for level, msg in st.messages:
        print(f"[{level}] {msg}")


if __name__ == "__main__":
    pilo.run_main(main)
