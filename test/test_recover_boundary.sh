#!/bin/sh
set -e

DATA_ROOT=$TEST_ROOT
REPL_ROOT=$TEST_REPLICA

echo pile > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile
echo temp > /tank/data/stash/temp.txt
zfs snapshot -r $DATA_ROOT@baseline
system-replicate $DATA_ROOT $REPL_ROOT
zfs destroy -r $DATA_ROOT

system-recover-baseline $REPL_ROOT/active/pile-readonly \
                        $DATA_ROOT/active/pile-readonly baseline >/dev/null

assert_grep pile < /tank/data/active/pile-readonly/.zfs/snapshot/baseline/file.txt
assert_not_exists /tank/data/stash/temp.txt
