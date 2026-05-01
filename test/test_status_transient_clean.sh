#!/bin/sh
set -e

workdir=/$ADMIN/work
mkdir $workdir
cd $workdir
git init -q
echo data > file.txt
git add file.txt
git commit -m init -q

capture_status pilo-status transient

assert_command_ok expected clean transient state
