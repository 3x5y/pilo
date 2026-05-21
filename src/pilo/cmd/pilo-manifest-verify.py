#!/usr/bin/env python3

import sys

from pilo import context
from pilo import error
from pilo import lifecycle
from pilo import status


def main():
    cx = context.Context()
    report = lifecycle.ValidationReport()
    report.extend(status.collect_manifest_validation(cx))
    for line in status.render_validation_report(report):
        print(line)
    sys.exit(report.exit_code)


if __name__ == "__main__":
    error.run_main(main)
