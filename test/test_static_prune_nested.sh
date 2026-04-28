#!/bin/sh
set -e

with_writable $PILE \
    mkdir -p /$PILE/out/collection/a/b/c

system-prune-pile

assert_not_exists /$PILE/out/collection/a/b/c
assert_not_exists /$PILE/out/collection/a/b
assert_not_exists /$PILE/out/collection/a
