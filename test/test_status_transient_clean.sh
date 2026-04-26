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
[ $STATUS -eq 0 ] || fail expected clean transient state
