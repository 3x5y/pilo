#!/bin/sh
set -e

pilo-snapshot t0
pilo-replicate

OUTPUT=$(pilo-replication-verify)

echo "$OUTPUT" | assert_grep "^STATUS=OK"
