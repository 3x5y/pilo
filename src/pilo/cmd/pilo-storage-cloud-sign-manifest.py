#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage.cloud import sign_cloud_manifest


def main():
    args = sys.argv[1:]

    if len(args) != 2:
        print(
            "Usage: pilo storage-cloud-sign-manifest "
            "<keyfile> <manifest>",
            file=sys.stderr,
        )
        sys.exit(1)

    keyfile = Path(args[0])
    manifest_path = Path(args[1])

    try:
        sig_path = sign_cloud_manifest(manifest_path, keyfile)
    except ValueError as e:
        error.fatal(str(e))

    print(sig_path)


if __name__ == "__main__":
    error.run_main(main)
