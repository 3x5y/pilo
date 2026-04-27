#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

with_writable $PILE mkdir -p /$PILE/out/collection/a
with_writable $PILE sh -c "echo data > /$PILE/out/collection/a/file.txt"

system-prune-pile

assert_dir_exists /$PILE/out/collection/a
