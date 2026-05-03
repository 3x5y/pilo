#!/bin/sh
set -eu

with_writable $COLLECTION \
    touch "$PILO_STATIC_PATH"/collection/a.txt

pilo manifest-update

manifest="$PILO_ADMIN_PATH/manifest/collection.manifest"
assert_file_exists "$manifest"
assert_grep " \\./a.txt" < "$manifest"
