#!/bin/sh
set -e

echo "pile" > /tank/data/active/pile/p.txt
echo "archive" > /tank/data/archive/a.txt

zfs snapshot tank/data/active/pile@t1

# Verify archive is NOT snapshot-protected
if [ -f /tank/data/archive/.zfs/snapshot/t1/a.txt ]
then
    echo "FAIL: archive incorrectly snapshot"
    exit 1
fi
