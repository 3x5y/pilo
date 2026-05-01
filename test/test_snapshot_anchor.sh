#!/bin/sh
set -e

pilo-snapshot-anchor

zfs list -t snapshot | assert_grep "@a-"
