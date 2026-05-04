#!/usr/bin/env python3

import subprocess

import pilo


# unused; kept for reference
def __prune_empty_dirs(root):
    # walk bottom-up
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass  # not empty


def main():
    cx = pilo.Context()
    args = "-mindepth 2 -type d -empty -delete"
    cmd = ["find", cx.pile_path] + args.split()
    with pilo.dataset_writable(cx.pile_dataset):
        subprocess.run(cmd, check=True)
        #prune_empty_dirs(cx.pile_path)


if __name__ == "__main__":
    main()
