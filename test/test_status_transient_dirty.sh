#!/bin/sh
set -e

WORKDIR=/$ACTIVE/admin/work
mkdir $WORKDIR
cd $WORKDIR
git init -q
echo data > file.txt
git add file.txt
git commit -m init -q
echo change >> file.txt

capture_status system-status transient

assert_command_fail status returned success
echo "$OUTPUT" | assert_grep transient

