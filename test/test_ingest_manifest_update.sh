#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
FILE=file.txt

echo data > /tmp/$FILE

system-capture /tmp/$FILE
system-ingest-pile

assert_file_exists $PILE/in/$FILE

# manifest must contain correct checksum entry
(cd $PILE && sha256sum --quiet --strict -c .manifest)
grep -q " \./in/$FILE$" $PILE/.manifest || fail "missing manifest entry"
