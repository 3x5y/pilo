#!/bin/sh
set -e

file=file.txt

mkfile data $file
capture_file $file
pilo content-ingest

manifest="$PILO_ADMIN_PATH"/manifest/pile.manifest

cp $manifest $TMP/manifest_before

# re-upload identical file
mkintake data $file
pilo content-ingest

diff -u $TMP/manifest_before $manifest \
    || fail "manifest changed on idempotent ingest"
