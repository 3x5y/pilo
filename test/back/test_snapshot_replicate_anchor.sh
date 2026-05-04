#!/bin/sh
set -e

pilo snapshot-anchor
pilo replicate

zfs list -t snapshot | assert_grep "$TEST_REPLICA@a-"
