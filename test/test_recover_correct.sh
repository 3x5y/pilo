#!/bin/sh
set -e

repl=$TEST_REPLICA/active/pile-readonly
snap=baseline
mkfile critical file.txt
capture_file file.txt
system-ingest-pile
system-manifest-update
system-snapshot $snap
system-replicate
zfs destroy -r $TEST_ROOT

system-recover-baseline $repl $PILE $snap >/dev/null

capture_status system-manifest-verify
assert_command_ok manifest verification failed after recovery
