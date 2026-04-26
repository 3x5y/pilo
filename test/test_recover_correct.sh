#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly
REPL=$TEST_REPLICA/pile-readonly

echo critical > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile
system-manifest-update
zfs snapshot $SRC@baseline
system-replicate $SRC $REPL
zfs destroy -r $TEST_ROOT

system-recover-baseline $REPL $SRC baseline >/dev/null

capture_status system-manifest-verify
assert_command_ok manifest verification failed after recovery
