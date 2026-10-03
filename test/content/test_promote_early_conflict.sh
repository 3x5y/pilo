#!/bin/sh
set -eu

# existing static file
with_writable $COLLECTION \
    sh -c "echo A > '/$STATIC/collection/x.txt'"

# conflicting file in pile
with_writable $PILE \
    sh -c "echo B > '/$PILE/out/collection/x.txt'"

capture_status pilo content-promote

assert_command_fail "promote should fail on conflict"

# ensure source still exists (no partial delete)
assert_file_exists /"$PILE/out/collection/x.txt"
