#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly
REPL=$TEST_REPLICA/pile-readonly

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

zfs snapshot $SRC@baseline

# deliberately skip replication

zfs destroy -r $TEST_ROOT

capture_status system-recover-baseline $REPL $SRC baseline
assert_command_fail
