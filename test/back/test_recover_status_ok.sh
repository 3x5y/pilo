#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-replica-seed

clear_holds
zfs destroy -r $TEST_ROOT

pilo storage-recover >/dev/null

capture_status pilo status

assert_command_ok
