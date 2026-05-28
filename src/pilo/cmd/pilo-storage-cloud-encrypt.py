#!/usr/bin/env python3

import sys
from dataclasses import replace
from pathlib import Path

from pilo import error
from pilo.storage.cloud import (
    encrypt_archive,
    load_package_manifest,
    write_package_manifest,
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

    encrypted_path, encrypted_archive = encrypt_archive(
        archive_path, dst_dir, recipient, identity=identity,
    )

    stamp = archive_path.name.removesuffix(".tar.zst")
    src_manifest_path = archive_path.parent / f"{stamp}.tar.zst.manifest"
    manifest = load_package_manifest(src_manifest_path)

    manifest = replace(
        manifest,
        recipient=recipient,
        encrypted_archive=encrypted_archive,
    )

    age_manifest_path = dst_dir / f"{stamp}.tar.zst.age.manifest"
    write_package_manifest(manifest, age_manifest_path)

    print(encrypted_path)


if __name__ == "__main__":
    error.run_main(main)
