#!/usr/bin/env python3

import os
import subprocess
import sys

from pilo import fatal, Context


def verify_manifest(cx, subset):
    if subset == 'pile':
        base_dir = cx.pile_path
    elif subset in ('collection', 'filing'):
        base_dir = os.path.join(cx.static_path, subset)
    else:
        raise Exception(f"Unsupported subset '{subset}'")

    manifest = os.path.join(cx.admin_path, "manifest", f"{subset}.manifest")

    # equivalent to [ -s "$manifest" ] || return 0
    if not os.path.isfile(manifest) or os.path.getsize(manifest) == 0:
        return

    try:
        subprocess.run(
            ["sha256sum", "--quiet", "--strict", "-c", manifest],
            cwd=base_dir,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        # preserve shell behaviour: just fail
        sys.exit(e.returncode)


def main():
    cx = Context(os.environ)
    verify_manifest(cx, "pile")
    verify_manifest(cx, "collection")
    verify_manifest(cx, "filing")


if __name__ == "__main__":
    main()
