#!/bin/sh
set -eu

with_writable $PILE \
    rmdir "$PILO_PILE_PATH/in"

capture_status pilo doctor

assert_command_fail
echo "$OUTPUT" | assert_grep "missing directory"
