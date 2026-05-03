#!/usr/bin/env python3

import os
import subprocess
import sys


def fatal(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def verify_manifest(subset, base_dir):
    admin_path = os.environ.get("PILO_ADMIN_PATH")
    if not admin_path:
        fatal("PILO_ADMIN_PATH not set")

    manifest = os.path.join(admin_path, "manifest", f"{subset}.manifest")

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
    pile_path = os.environ.get("PILO_PILE_PATH")
    static_path = os.environ.get("PILO_STATIC_PATH")

    if not pile_path or not static_path:
        fatal("environment not configured")

    verify_manifest("pile", pile_path)
    verify_manifest("collection", os.path.join(static_path, "collection"))
    verify_manifest("filing", os.path.join(static_path, "filing"))


if __name__ == "__main__":
    main()
