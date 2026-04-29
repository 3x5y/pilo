#!/bin/sh
set -e

system-snapshot t0
system-replicate

system-snapshot t1

capture_status system-replicate-safe

assert_command_ok expected catch-up replication
