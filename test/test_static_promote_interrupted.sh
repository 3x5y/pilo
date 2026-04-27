#!/bin/sh
set -e

FILE=file.txt

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

# simulate interrupted promotion
with_writable tank/data/static \
    cp /tank/data/active/pile-readonly/in/$FILE /tank/data/static/collection/

# now run promote again
system-static-promote in/$FILE collection

# invariant: only exists in static
assert_not_exists /tank/data/active/pile-readonly/in/$FILE
assert_file_exists /tank/data/static/collection/$FILE
