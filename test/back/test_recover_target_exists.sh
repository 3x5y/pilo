#!/bin/sh
set -e

snap=baseline

echo data > /$ADMIN/file.txt
pilo snapshot $snap
pilo replicate

# DO NOT destroy destination → it still exists

capture_status pilo recover $ADMIN

assert_command_fail
echo "$OUTPUT" | assert_grep "destination exists"
