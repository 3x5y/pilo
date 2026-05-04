#!/usr/bin/env python3

from pathlib import Path

import pilo


def main():
    cx = pilo.Context()

    if len(cx.args) < 2:
        pilo.fatal("missing arguments")

    src = Path(cx.args[0])
    dst_rel = Path(cx.args[1])

    if not src.is_file():
        pilo.fatal(f"source file missing: {src}")

    resolved = cx.resolve(dst_rel)

    if not resolved.path.is_file():
        pilo.fatal(f"target does not exist: {dst_rel}")

    with pilo.dataset_writable(resolved.dataset):
        cx.copy(src, resolved.path)

    pilo.run(["pilo", "manifest-update"])


if __name__ == "__main__":
    main()
