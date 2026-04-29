#!/bin/sh
set -e

system-snapshot t0
system-replicate

capture_status system-replicate-safe

assert_command_ok expected no-op
