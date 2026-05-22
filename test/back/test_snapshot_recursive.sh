#!/bin/sh
set -e

pilo snapshot-rpo

zfs list -t snapshot -Ho name | assert_grep "$ADMIN.*-incr$"
zfs list -t snapshot -Ho name | assert_grep "$COLLECTION.*-incr$"
