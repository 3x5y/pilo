#!/bin/sh
set -e

with_writable $PILE \
    mkdir -p /$PILE/out/collection

capture_status system-static-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "out.*empty"
