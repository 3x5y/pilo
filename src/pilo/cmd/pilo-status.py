#!/usr/bin/env python3

from pilo import context, error, status


def main():
    cx = context.Context()
    check = cx.args[0] if cx.args else None
    st = status.collect_system_status(cx, check=check)

    for sm in st.messages:
        print(status.render_status_message(sm))

    exit(st.code)


if __name__ == "__main__":
    error.run_main(main)
