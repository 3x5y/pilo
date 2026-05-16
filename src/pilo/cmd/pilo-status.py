#!/usr/bin/env python3

from pilo import context
from pilo import error
from pilo import status


def main():
    cx = context.Context()
    check = cx.args[0] if cx.args else None
    st = status.collect_system_status(cx, check=check)

    for msg in status.render_system_status(st):
        print(msg)

    exit(st.code)


if __name__ == "__main__":
    error.run_main(main)
