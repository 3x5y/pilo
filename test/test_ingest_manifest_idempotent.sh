#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
FILE=file.txt

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

cp $PILE/.manifest /tmp/manifest_before

# re-upload identical file
echo data > /tank/data/active/pile-intake/$FILE
system-ingest-pile

cmp /tmp/manifest_before $PILE/.manifest \
    || fail "manifest changed on idempotent ingest"
