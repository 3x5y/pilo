#!/bin/sh
set -e

system-snapshot t0
system-replicate
system-replicate

capture_status system-replication-verify

assert_command_ok replication should remain valid
