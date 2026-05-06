#!/bin/sh
set -e

repl=$TEST_REPLICA/active/pile-readonly
snap=baseline
mkfile critical file.txt
capture_file file.txt
pilo ingest-pile
pilo manifest-update
pilo snapshot $snap
pilo replicate
zfs destroy -r $PILE

pilo restore $repl $PILE $snap

capture_status pilo manifest-verify
assert_command_ok manifest verification failed after recovery
