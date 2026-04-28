#!/bin/sh
set -e

dir=random
with_writable $PILE \
    mkdir -p /$PILE/out/$dir
with_writable $PILE \
    touch /$PILE/out/$dir/file.txt

capture_status system-static-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid /out/ structure"
