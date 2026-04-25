#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile
REPL=$TEST_REPLICA/pile

echo important > /tank/data/active/pile/file.txt
zfs snapshot $SRC@baseline

system-replicate $SRC $REPL

zfs destroy -r $TEST_ROOT

system-recover-baseline $REPL $SRC baseline >/dev/null

assert_grep important < /$SRC/.zfs/snapshot/baseline/file.txt
