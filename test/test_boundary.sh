#!/bin/sh
set -e

# canonical
echo "important" > /tank/data/active/pile/canon.txt

# non-canonical (stash)
echo "temporary" > /tank/data/stash/temp.txt

# snapshot canonical dataset
zfs snapshot tank/data/active/pile@canon_test

# verify canonical file exists in snapshot
if [ ! -f /tank/data/active/pile/.zfs/snapshot/canon_test/canon.txt ]; then
    echo "FAIL: canonical not protected"
    exit 1
fi

# stash is NOT covered (by policy, not mechanics yet)
# (we're not enforcing, just observing separation)
