#!/usr/bin/env python3

import subprocess

from pilo import fatal, Context


def verify_manifest(cx, subset):
    if subset == 'pile':
        base_dir = cx.pile_path
    elif subset in ('collection', 'filing'):
        base_dir = cx.static_path / subset
    else:
        raise Exception(f"Unsupported subset '{subset}'")

    manifest = cx.admin_path / "manifest" / f"{subset}.manifest"

    # equivalent to [ -s "$manifest" ] || return 0
    if not manifest.is_file() or manifest.stat().st_size == 0:
        return

    try:
        subprocess.run(
            ["sha256sum", "--quiet", "--strict", "-c", manifest],
            cwd=str(base_dir),
            check=True,
        )
    except subprocess.CalledProcessError as e:
        # preserve shell behaviour: just fail
        exit(e.returncode)


def main():
    cx = Context()
    verify_manifest(cx, "pile")
    verify_manifest(cx, "collection")
    verify_manifest(cx, "filing")


if __name__ == "__main__":
    main()
