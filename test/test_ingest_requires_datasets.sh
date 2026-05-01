#!/bin/sh
set -eu

zfs destroy -r $TEST_ROOT/active/pile-readonly

echo data > /$TEST_ROOT/active/pile-intake/file.txt

capture_status system-ingest-pile

assert_command_fail "ingest should fail without pile dataset"
echo "$OUTPUT" | assert_grep "missing required dataset"
