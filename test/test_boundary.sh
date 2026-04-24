#!/bin/sh
set -e

echo "important" > /tank/data/active/pile/canon.txt
echo "temporary" > /tank/data/stash/temp.txt

zfs snapshot tank/data/active/pile@canon_test

# verify canonical file exists in snapshot
if [ ! -f /tank/data/active/pile/.zfs/snapshot/canon_test/canon.txt ]
then
    echo "FAIL: canonical not protected"
    exit 1
fi

# stash must NOT appear in canonical snapshot
if [ -f /tank/data/active/pile/.zfs/snapshot/canon_test/temp.txt ]
then
    echo "FAIL: non-canonical data leaked into canonical snapshot"
    exit 1
fi
