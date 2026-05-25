#!/bin/sh
set -e

zfs destroy -r $TEST_ROOT

capture_status pilo storage-provision-primary

assert_command_ok

zfs list $TEST_ROOT >/dev/null || fail "missing dataset"
zfs list $TEST_ROOT/active/admin >/dev/null || fail "missing dataset"
zfs list $TEST_ROOT/active/pile-readonly >/dev/null || fail "missing dataset"
zfs list $TEST_ROOT/static/collection >/dev/null || fail "missing dataset"
