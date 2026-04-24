#!/bin/sh
set -e

SRC="$TEST_ROOT/active/pile"
DST="$TEST_REPLICA/pile"

# initial state
echo "v1" > /tank/data/active/pile/file.txt
zfs snapshot "$SRC@t0"
zfs send "$SRC@t0" | zfs receive "$DST"

# change
echo "v2" > /tank/data/active/pile/file.txt
zfs snapshot "$SRC@t1"

# incremental send
zfs send -i "$SRC@t0" "$SRC@t1" | zfs receive "$DST"

# verify latest snapshot exists
zfs list -t snapshot | grep -q "$DST@t1"

# verify updated content
if ! grep -q "v2" "/$DST/.zfs/snapshot/t1/file.txt"; then
    echo "FAIL: incremental update not applied"
    exit 1
fi
