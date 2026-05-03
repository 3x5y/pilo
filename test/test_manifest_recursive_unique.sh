#!/bin/sh
set -e

mkintake data a/file.txt
mkintake data b/file.txt

pilo ingest-pile

manifest="$PILO_ADMIN_PATH"/manifest/pile.manifest
count=$(grep -c "file.txt$" $manifest)
[ "$count" -eq 2 ] || fail "expected two distinct entries"
