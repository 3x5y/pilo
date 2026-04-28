#!/bin/sh
set -e

with_writable $PILE mkdir -p /$PILE/in
with_writable $PILE mkdir -p /$PILE/out
with_writable $PILE mkdir -p /$PILE/sort

system-prune-pile

assert_dir_exists /$PILE/in
assert_dir_exists /$PILE/out
assert_dir_exists /$PILE/sort
