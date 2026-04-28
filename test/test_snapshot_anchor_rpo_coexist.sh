#!/bin/sh
set -e

system-snapshot-anchor
system-snapshot-rpo

zfs list -t snapshot | assert_grep "@a-"
zfs list -t snapshot | assert_grep "@r-"
