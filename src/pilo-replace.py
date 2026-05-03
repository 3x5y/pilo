#!/usr/bin/env python3

import os
import sys
from pathlib import Path

import pilo


def resolve(cx, rel: Path):
    parts = rel.parts

    if parts[0] == "in":
        return cx.pile_path / rel, cx.pile_dataset

    if parts[0] == "collection":
        return cx.static_path / rel, f"{cx.static_dataset}/collection"

    if parts[0] == "filing":
        if len(parts) < 2:
            pilo.fatal("invalid filing path")
        dataset = f"{cx.static_dataset}/filing/{parts[1]}"
        return cx.static_path / rel, dataset

    pilo.fatal("invalid target path")


def main():
    cx = pilo.Context(os.environ, sys.argv)

    if len(cx.args) < 2:
        pilo.fatal("missing arguments")

    src = Path(cx.args[0])
    dst_rel = Path(cx.args[1])

    if not src.is_file():
        pilo.fatal(f"source file missing: {src}")

    dst, dataset = resolve(cx, dst_rel)

    if not dst.is_file():
        pilo.fatal(f"target does not exist: {dst_rel}")

    def do_replace():
        cx.copy(src, dst)

    with pilo.dataset_writable(dataset):
        do_replace()

    pilo.run(["pilo", "manifest-update"])


if __name__ == "__main__":
    main()
