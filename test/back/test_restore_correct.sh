#!/bin/sh
set -e

repl=$TEST_REPLICA/active/pile-readonly
snap=baseline
mkfile critical file.txt
capture_file file.txt
pilo content-ingest
pilo storage-snapshot $snap
pilo storage-replica-seed
clear_holds $PILE
zfs destroy -r $PILE

pilo storage-restore $repl $PILE $snap

capture_status pilo manifest-verify
assert_command_ok manifest verification failed after recovery
