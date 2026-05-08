#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()
    check = cx.args[0] if cx.args else None
    st = pilo.collect_system_status(cx, check=check)

    for sm in st.messages:
        print(f"[{sm.level}] {sm.message}")

    exit(st.code)


if __name__ == "__main__":
    pilo.run_main(main)
