#!/bin/sh
set -e

system-snapshot t0
system-replicate $TEST_ROOT $TEST_REPLICA

capture_status system-replicate $TEST_ROOT $TEST_REPLICA
assert_command_success
