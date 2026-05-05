#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()

    if len(cx.args) != 3:
        pilo.fatal("usage: recover-tree SRC DST SNAP")

    src, dst, snap = cx.args
    pilo.recover_dataset(
        src_snap=f"{src}@{snap}",
        dst=dst,
        recursive=True,
    )


if __name__ == "__main__":
    main()
