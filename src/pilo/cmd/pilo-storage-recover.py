#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import status
from pilo.storage import recover


def main():
    cx = context.Context()

    target = cx.args[0] if cx.args else cx.root_dataset
    stream_dir = cx.args[1] if len(cx.args) > 1 else None

    plan = recover.build_recovery_plan(cx, target, stream_dir=stream_dir)
    recover.execute_recovery_plan(plan, cx)

    report = status.collect_report(cx)
    for msg in status.render_validation_report(report):
        print(msg)

    #exit(report.exit_code)


if __name__ == "__main__":
    error.run_main(main)
