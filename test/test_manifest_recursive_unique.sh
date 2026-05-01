#!/bin/sh
set -e

mkintake data a/file.txt
mkintake data b/file.txt

pilo ingest-pile

count=$(grep -c "file.txt$" /$PILE/.manifest)
[ "$count" -eq 2 ] || fail "expected two distinct entries"
