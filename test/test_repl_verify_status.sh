#!/bin/sh
set -e

system-snapshot t0
system-replicate

OUTPUT=$(system-replication-verify)

echo "$OUTPUT" | assert_grep "^STATUS=OK"
