#!/usr/bin/env python3

import sys

import pilo


def main():
    cx = pilo.Context()
    st = pilo.SystemStatus()
    pilo.check_manifest_status(cx, st)
    for line in pilo.render_system_status(st):
        print(line)
    sys.exit(st.code)


if __name__ == "__main__":
    pilo.run_main(main)
