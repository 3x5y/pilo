#!/bin/sh
set -eu

archive=filing/2025
zfs create -p $STATIC/$archive
chown $PILO_USER:$PILO_USER /$STATIC/$archive
with_writable $STATIC \
    touch "$PILO_STATIC_PATH"/filing/2025/doc.txt

pilo manifest-update

assert_manifest_entry filing " \\./2025/doc.txt"
