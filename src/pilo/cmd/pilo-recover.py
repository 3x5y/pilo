#!/usr/bin/env python3

from pilo import context, error, status
from pilo.back import recover


def main():
    cx = context.Context()

    if cx.args:
        target = cx.args[0]
    else:
        target = cx.root_dataset

    plan = recover.build_recovery_plan(cx, target)
    recover.execute_recovery_plan(plan, cx)

    st = status.collect_system_status(cx)
    for sm in st.messages:
        print(f"[{sm.level}] {sm.message}")


if __name__ == "__main__":
    error.run_main(main)
