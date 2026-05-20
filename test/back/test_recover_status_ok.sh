#!/bin/sh
set -e

pilo snapshot t0
pilo replica-seed

clear_holds
zfs destroy -r $TEST_ROOT

pilo recover >/dev/null

capture_status pilo status

assert_command_ok
