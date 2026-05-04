#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
pilo ingest-pile

manifest="$PILO_ADMIN_PATH"/manifest/pile.manifest

cp $manifest $TMP/manifest_before

# re-upload identical file
mkintake data $file
pilo ingest-pile

diff -u $TMP/manifest_before $manifest \
    || fail "manifest changed on idempotent ingest"
