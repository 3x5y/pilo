#!/bin/sh
set -e

file=bad.txt
echo data > /$PILE/out/filing/$file

capture_status pilo content-promote

assert_command_fail accepted invalid structure
echo "$OUTPUT" | assert_grep "invalid filing structure"
