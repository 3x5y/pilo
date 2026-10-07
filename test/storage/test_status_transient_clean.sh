#!/bin/sh
set -e

workdir=/$ADMIN/work
runuser mkdir $workdir
cd $workdir
runuser git init -q
runuser touch file.txt
runuser git add file.txt
runuser git commit -m init -q

capture_status pilo status transient

assert_command_ok expected clean transient state
