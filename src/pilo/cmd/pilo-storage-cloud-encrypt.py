#!/usr/bin/env python3

import sys
from pathlib import Path

from pilo import error
from pilo.storage.cloud import (
    encrypt_archive,
    write_cloud_manifest,
)


def main():
    args = sys.argv[1:]

    identity = None
    while args and args[0].startswith("--"):
        opt = args.pop(0)
        if opt == "--identity":
            if not args:
                print("--identity requires an argument", file=sys.stderr)
                sys.exit(1)
            identity = args.pop(0)
        else:
            print(f"unknown option: {opt}", file=sys.stderr)
            sys.exit(1)

    if len(args) != 3:
        print(
            "Usage: pilo storage-cloud-encrypt [--identity <keyfile>] "
            "<recipient> <archive.tar.zst> <output-dir>",
            file=sys.stderr,
        )
        sys.exit(1)

    recipient = args[0]
    archive_path = Path(args[1])
    dst_dir = Path(args[2])

    try:
        encrypted_path, cloud_manifest = encrypt_archive(
            archive_path, dst_dir, recipient, identity=identity,
        )
    except ValueError as e:
        error.fatal(str(e))

    stamp = archive_path.name.removesuffix(".tar.zst")
    age_manifest_path = dst_dir / f"{stamp}.tar.zst.age.manifest"
    write_cloud_manifest(cloud_manifest, age_manifest_path)

    print(encrypted_path)


if __name__ == "__main__":
    error.run_main(main)
