#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import status


def main():
    cx = context.Context()
    check = cx.args[0] if cx.args else None

    report = status.collect_report(cx, check=check)
    for msg in status.render_validation_report(report):
        print(msg)

    exit(report.exit_code)


if __name__ == "__main__":
    error.run_main(main)
