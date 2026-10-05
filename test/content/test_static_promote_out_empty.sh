#!/bin/sh
set -e

mkdir -p /$PILE/out/collection

capture_status pilo content-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "out.*empty"
