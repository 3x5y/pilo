#!/bin/sh
set -e

# simulate policy
zfs set com.test:snapshot=frequent tank/data/active/pile
zfs set com.test:snapshot=rare tank/data/archive

PILE_POLICY=$(zfs get -H -o value com.test:snapshot tank/data/active/pile)
ARCHIVE_POLICY=$(zfs get -H -o value com.test:snapshot tank/data/archive)

if [ "$PILE_POLICY" = "$ARCHIVE_POLICY" ]; then
    echo "FAIL: policies not distinct"
    exit 1
fi
