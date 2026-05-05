#!/bin/sh
set -e

pilo snapshot t0
pilo replicate

zfs destroy -r $ADMIN
zfs destroy -r $PILE

# recover only admin
pilo recover $ADMIN >/dev/null

capture_status pilo status

assert_command_fail
echo "$OUTPUT" | assert_grep incomplete
