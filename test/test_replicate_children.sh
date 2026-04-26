#!/bin/sh
set -e

ROOT=$TEST_ROOT
DST=$TEST_REPLICA
PILE=$TEST_ROOT/active/pile-readonly
STATIC=$TEST_ROOT/static

with_dataset_writable $PILE sh -c "echo v1 > /$PILE/file.txt"
with_dataset_writable $STATIC sh -c "echo a1 > /$STATIC/doc.txt"
system-snapshot t0

system-replicate $ROOT $DST
with_dataset_writable $PILE sh -c "echo v2 > /$PILE/file.txt"
with_dataset_writable $STATIC sh -c "echo a2 > /$STATIC/doc.txt"
system-snapshot t1

system-replicate $ROOT $DST

assert_grep v2 < /$DST/active/pile-readonly/.zfs/snapshot/t1/file.txt
assert_grep a2 < /$DST/static/.zfs/snapshot/t1/doc.txt
