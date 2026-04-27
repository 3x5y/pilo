#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

with_writable $PILE \
    mkdir -p /$PILE/out/random
with_writable $PILE \
    sh -c "echo data > /$PILE/out/random/file.txt"

capture_status system-static-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid /out/ structure"
