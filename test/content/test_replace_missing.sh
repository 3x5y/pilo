#!/bin/sh
set -eu

echo new > "$TMP/new.txt"

capture_status pilo content-replace "$TMP/new.txt" in/missing.txt

assert_command_fail
echo "$OUTPUT" | assert_grep "does not exist"
