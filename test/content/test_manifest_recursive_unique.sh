#!/bin/sh
set -e

mkdir /$PILE/in/a
mkdir /$PILE/in/b
echo data > /$PILE/in/a/file.txt
echo data > /$PILE/in/b/file.txt
create_pile_manifest

manifest=/"$ADMIN"/manifest/pile.manifest
count=$(grep -c "file.txt$" $manifest)
[ "$count" -eq 2 ] || fail "expected two distinct entries"
