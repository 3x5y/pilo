#!/bin/sh
set -e

with_writable $PILE \
    mkdir -p /$PILE/out/collection/a
with_writable $PILE \
    touch /$PILE/out/collection/a/file.txt

system-prune-pile

assert_dir_exists /$PILE/out/collection/a
