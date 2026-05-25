#!/bin/sh
set -e

pilo snapshot-reg
pilo snapshot-reg
pilo replica-seed

zfs list -t snap -Ho name $TEST_REPLICA | assert_grep "reg$"
