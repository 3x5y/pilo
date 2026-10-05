#!/bin/sh
set -e

dir=random
mkdir -p /$PILE/out/$dir
touch /$PILE/out/$dir/file.txt

capture_status pilo content-promote

assert_command_fail
echo "$OUTPUT" | assert_grep "invalid /out/ structure"
