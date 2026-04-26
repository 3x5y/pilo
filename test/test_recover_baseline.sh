#!/bin/sh
set -e

SRC=$TEST_ROOT/active/pile-readonly
REPL=$TEST_REPLICA/pile-readonly

echo important > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile
zfs snapshot $SRC@baseline
system-replicate $SRC $REPL
zfs destroy -r $TEST_ROOT

system-recover-baseline $REPL $SRC baseline >/dev/null

assert_grep important < /$SRC/.zfs/snapshot/baseline/file.txt
