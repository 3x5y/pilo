#!/bin/sh
set -eu

# existing static file
with_writable $COLLECTION \
    sh -c "echo A > '$PILO_STATIC_PATH/collection/x.txt'"

# conflicting file in pile
#mkdir -p "$PILO_PILE_PATH/out/collection"
with_writable $PILE \
    sh -c "echo B > '$PILO_PILE_PATH/out/collection/x.txt'"

capture_status pilo static-promote

assert_command_fail "promote should fail on conflict"

# ensure source still exists (no partial delete)
assert_file_exists "$PILO_PILE_PATH/out/collection/x.txt"
