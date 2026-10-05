#!/bin/sh
set -e

repl=$TEST_REPLICA/pile
snap=baseline

echo critical > /$PILE/in/file.txt
create_pile_manifest

pilo storage-snapshot $snap
pilo storage-replica-seed
clear_holds $PILE
zfs destroy -r $PILE

pilo storage-restore $repl $PILE $snap
zfs set mountpoint=/$PILE $PILE

capture_status pilo manifest-verify
assert_command_ok manifest verification failed after recovery
