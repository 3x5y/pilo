#!/bin/sh
set -e

WORKDIR=/tank/data/active/admin-work
mkdir -p $WORKDIR
cd $WORKDIR
git init -q

echo data > file.txt
git add file.txt
git commit -m init -q

capture_status system-status transient
assert_command_ok expected clean transient state
