#!/bin/sh
set -e

workdir=/$ADMIN/work
mkdir $workdir
cd $workdir
git init -q
echo data > file.txt
git add file.txt
git commit -m init -q
echo change >> file.txt

capture_status pilo-status transient

assert_command_fail status returned success
echo "$OUTPUT" | assert_grep transient

