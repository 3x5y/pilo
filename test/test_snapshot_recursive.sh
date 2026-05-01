#!/bin/sh
set -e

pilo-snapshot-anchor

zfs list -t snapshot | assert_grep "$ADMIN@a-"
zfs list -t snapshot | assert_grep "$COLLECTION@a-"
