#!/bin/sh
set -e

FILE=file.txt
PILE=tank/data/active/pile-readonly

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

# simulate interrupted promotion
with_writable tank/data/static \
    cp /tank/data/active/pile-readonly/in/$FILE /tank/data/static/collection/

# now run promote again
with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/collection
system-static-promote

# invariant: only exists in static
assert_not_exists /tank/data/active/pile-readonly/out/collection/$FILE
assert_file_exists /tank/data/static/collection/$FILE
