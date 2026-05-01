#!/bin/sh
set -e

pilo snapshot t0

capture_status pilo status replication

assert_command_fail expected replication warning
echo "$OUTPUT" | assert_grep replication
