#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
system-ingest-pile

cp /$PILE/.manifest $TMP/manifest_before

# re-upload identical file
mkintake data $file
system-ingest-pile

diff -u /tmp/manifest_before /$PILE/.manifest \
    || fail "manifest changed on idempotent ingest"
