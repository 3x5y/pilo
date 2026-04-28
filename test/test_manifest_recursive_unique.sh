#!/bin/sh
set -e

mkintake data a/file.txt
mkintake data b/file.txt

system-ingest-pile

COUNT=$(grep -c "file.txt$" /$PILE/.manifest)
[ "$COUNT" -eq 2 ] || fail "expected two distinct entries"
