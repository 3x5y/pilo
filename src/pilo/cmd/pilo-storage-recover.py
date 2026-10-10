#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import status
from pilo.storage import recover


def main():
    cx = context.Context()

    target = cx.args[0] if cx.args else cx.root_dataset
    plan = recover.build_recovery_plan(cx, target)
    recover.execute_recovery_plan(plan, cx)
    print("RESTORE COMPLETE")

    print("VERIFY ...")
    report = status.collect_report(cx)
    for msg in status.render_validation_report(report):
        print(msg)

    if report.exit_code:
        print("RECOVERY INCOMPLETE: validation failed")
    else:
        print("RECOVERY COMPLETE: validation passed")

    raise SystemExit(report.exit_code)


if __name__ == "__main__":
    error.run_main(main)
