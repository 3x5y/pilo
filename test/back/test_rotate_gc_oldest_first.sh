#!/bin/sh
set -e

pilo storage-snapshot t0
pilo storage-snapshot t1
pilo storage-snapshot t2
pilo storage-replica-seed

OUT=$(pilo storage-rotate-gc --preview 2>&1)
echo "$OUT" | assert_grep "destroy"

pri=$(echo "$OUT" | grep "$TEST_ROOT")
first=$(echo "$pri" | sed -n '1p')
second=$(echo "$pri" | sed -n '2p')
echo "$first" | assert_grep "@t0"
echo "$second" | assert_grep "@t1"
