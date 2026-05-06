#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()
    check = cx.args[0] if cx.args else None
    st = pilo.collect_system_status(cx, check=check)

    for level, msg in st.messages:
        print(f"[{level}] {msg}")

    exit(st.code)


if __name__ == "__main__":
    main()
