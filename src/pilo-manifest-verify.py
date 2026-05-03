#!/usr/bin/env python3

import os
import subprocess
import sys

from pilo import fatal, require_env


def verify_manifest(subset, base_dir):
    admin_path = require_env("PILO_ADMIN_PATH")
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
    pile_path = require_env("PILO_PILE_PATH")
    static_path = require_env("PILO_STATIC_PATH")
    verify_manifest("pile", pile_path)
    verify_manifest("collection", os.path.join(static_path, "collection"))
    verify_manifest("filing", os.path.join(static_path, "filing"))


if __name__ == "__main__":
    main()
