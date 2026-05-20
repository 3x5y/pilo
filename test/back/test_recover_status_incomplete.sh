#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

clear_holds $ADMIN
clear_holds $PILE
zfs destroy -r $ADMIN
zfs destroy -r $PILE

# recover only admin
#pilo recover $ADMIN >/dev/null
capture_status pilo recover $ADMIN

assert_command_fail
echo "$OUTPUT" | assert_grep missing.required.dataset
