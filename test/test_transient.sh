#!/bin/sh
set -e

WORKDIR=/tank/data/active/admin-work
mkdir -p $WORKDIR
cd $WORKDIR
git init -q

echo data > file.txt
git add file.txt
git commit -m init -q

echo change >> file.txt

capture_status system-status

[ $STATUS -ne 0 ] || fail status returned success
echo "$OUTPUT" | assert_grep transient

