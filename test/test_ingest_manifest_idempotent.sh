#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
pilo ingest-pile

cp /$PILE/.manifest $TMP/manifest_before

# re-upload identical file
mkintake data $file
pilo ingest-pile

diff -u $TMP/manifest_before /$PILE/.manifest \
    || fail "manifest changed on idempotent ingest"
