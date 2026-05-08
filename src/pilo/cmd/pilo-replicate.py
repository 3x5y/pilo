#!/usr/bin/env python3

import pilo


def main():

    cx = pilo.Context()
    if cx.args:
        src, dst = cx.args
    else:
        src = cx.root_dataset
        dst = cx.replica_dataset

    return pilo.replicate(src, dst)


if __name__ == "__main__":
    pilo.run_main(main)
