#!/bin/sh
set -eu

archive=filing/2025
zfs create -p $STATIC/$archive
chown $PILO_USER:$PILO_USER /$STATIC/$archive
with_writable $STATIC \
    touch "$PILO_STATIC_PATH"/filing/2025/doc.txt

pilo manifest-update

manifest="$PILO_ADMIN_PATH/manifest/filing.manifest"

assert_file_exists "$manifest"
assert_grep " \\./2025/doc.txt" < "$manifest"
