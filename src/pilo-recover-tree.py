#!/usr/bin/env python3

import pilo


def main():
    cx = pilo.Context()

    if len(cx.args) != 3:
        pilo.fatal("usage: recover-tree SRC DST SNAP")

    src, dst, snap = cx.args
    src_snap = f"{src}@{snap}"
    pilo.restore_dataset(src_snap, dst, recursive=True)
    print(f"Restored {dst} from {src_snap}")


if __name__ == "__main__":
    main()
