#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

with_writable $PILE\
    mkdir -p /$PILE/out/collection

capture_status system-static-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "out.*empty"
