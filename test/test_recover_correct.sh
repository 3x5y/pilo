#!/bin/sh
set -e

echo critical > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile
system-manifest-update
system-snapshot baseline
system-replicate
zfs destroy -r $TEST_ROOT

system-recover-baseline $TEST_REPLICA/active/pile-readonly \
                        $TEST_ROOT/active/pile-readonly baseline >/dev/null

capture_status system-manifest-verify
assert_command_ok manifest verification failed after recovery
