#!/bin/sh
set -e

DATA_ROOT=$TEST_ROOT
REPL_ROOT=$TEST_REPLICA

zfs create -p $DATA_ROOT/active/pile
zfs create -p $DATA_ROOT/active/projects
zfs create -p $DATA_ROOT/archive

echo pile-data > /tank/data/active/pile/file.txt
echo project-data > /tank/data/active/projects/code.txt
echo archive-data > /tank/data/archive/doc.txt

zfs snapshot -r $DATA_ROOT@baseline

zfs send -R $DATA_ROOT@baseline | zfs receive -F $REPL_ROOT

zfs destroy -r $DATA_ROOT

system-recover-baseline $REPL_ROOT/active/pile \
                        $DATA_ROOT/active/pile baseline >/dev/null
system-recover-baseline $REPL_ROOT/active/projects \
                        $DATA_ROOT/active/projects baseline >/dev/null
system-recover-baseline $REPL_ROOT/archive \
                        $DATA_ROOT/archive baseline >/dev/null

assert_grep pile-data < /tank/data/active/pile/.zfs/snapshot/baseline/file.txt
assert_grep project-data < /tank/data/active/projects/.zfs/snapshot/baseline/code.txt
assert_grep archive-data < /tank/data/archive/.zfs/snapshot/baseline/doc.txt
