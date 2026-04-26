#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
FILE=file.txt

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

# simulate re-upload
echo data > /tank/data/active/pile-intake/$FILE
system-ingest-pile

# manifest still valid
(cd $PILE && sha256sum --quiet --strict -c .manifest)

# only one entry
COUNT=$(grep -c " ./$FILE$" $PILE/.manifest) \
    || fail "file not present in manifest"
[ "$COUNT" -eq 1 ] || fail "duplicate manifest entries"
