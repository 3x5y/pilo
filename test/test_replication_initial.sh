#!/bin/sh
set -e

SRC="$TEST_ROOT/active/pile"
DST="$TEST_REPLICA/pile"

# create data
echo "hello" > /tank/data/active/pile/file1.txt

# snapshot source
zfs snapshot "$SRC@t0"

# replicate
zfs send "$SRC@t0" | zfs receive "$DST"

# verify snapshot exists
zfs list -t snapshot | grep -q "$DST@t0"

# verify contents
if [ ! -f "/$DST/.zfs/snapshot/t0/file1.txt" ]; then
    echo "FAIL: file not present in replicated snapshot"
    exit 1
fi
