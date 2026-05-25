#!/bin/sh
set -eu

with_writable $PILE \
    sh -c "echo A > '$PILO_PILE_PATH/out/collection/a.txt'"
with_writable $PILE \
    sh -c "echo B > '$PILO_PILE_PATH/out/collection/b.txt'"

# create conflict only for one
with_writable $COLLECTION \
    sh -c 'echo X > "$PILO_STATIC_PATH/collection/a.txt"'

capture_status pilo content-promote
assert_command_fail

# neither should be moved
assert_file_exists "$PILO_PILE_PATH/out/collection/a.txt"
assert_file_exists "$PILO_PILE_PATH/out/collection/b.txt"
assert_not_exists $PILO_STATIC_PATH/collection/b.txt
assert_grep X < $PILO_STATIC_PATH/collection/a.txt
