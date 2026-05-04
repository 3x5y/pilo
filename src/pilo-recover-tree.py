#!/usr/bin/env python3

import sys
import pilo


def main():
    if len(sys.argv) < 4:
        pilo.fatal("usage: recover-tree SRC DST SNAP")

    src, dst, snap = sys.argv[1:4]
    #pilo.zfs_destroy(dst)
    pilo.zfs_send_recv(f"{src}@{snap}", dst, recursive=True)


if __name__ == "__main__":
    main()
