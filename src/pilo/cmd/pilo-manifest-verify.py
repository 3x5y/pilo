#!/usr/bin/env python3

import sys

from pilo import context, error, status


def main():
    cx = context.Context()
    st = status.SystemStatus()
    status.check_manifest_status(cx, st)
    for line in status.render_system_status(st):
        print(line)
    sys.exit(st.code)


if __name__ == "__main__":
    error.run_main(main)
