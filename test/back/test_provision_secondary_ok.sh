#!/bin/sh
set -e

zfs destroy -r $REPLICA_ROOT

capture_status pilo provision-secondary $REPLICA_ROOT

assert_command_ok

zfs list $REPLICA_ROOT >/dev/null || fail "missing dataset"

