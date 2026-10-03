#!/bin/sh
set -eu

with_writable $PILE \
    sh -c "echo A > '/$PILE/out/collection/a.txt'"
with_writable $PILE \
    sh -c "echo B > '/$PILE/out/collection/b.txt'"

# create conflict only for one
with_writable $COLLECTION \
    sh -c "echo X > '/$STATIC/collection/a.txt'"

capture_status pilo content-promote
assert_command_fail

# neither should be moved
assert_file_exists /"$PILE/out/collection/a.txt"
assert_file_exists /"$PILE/out/collection/b.txt"
assert_not_exists /$STATIC/collection/b.txt
assert_grep X < /$STATIC/collection/a.txt
