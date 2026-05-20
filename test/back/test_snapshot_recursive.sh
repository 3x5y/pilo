#!/bin/sh
set -e

pilo snapshot-rpo

zfs list -t snapshot | assert_grep "$ADMIN@r-"
zfs list -t snapshot | assert_grep "$COLLECTION@r-"
