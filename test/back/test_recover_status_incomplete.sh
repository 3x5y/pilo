#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

clear_holds $ADMIN
clear_holds $PILE
zfs destroy -r $ADMIN
zfs destroy -r $PILE

# recover only admin
#pilo storage-recover $ADMIN >/dev/null
capture_status pilo storage-recover $ADMIN

assert_command_fail
echo "$OUTPUT" | assert_grep missing.required.dataset
