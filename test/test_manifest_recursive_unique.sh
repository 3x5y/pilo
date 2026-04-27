#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly

mkdir -p /tank/data/active/pile-intake/a
mkdir -p /tank/data/active/pile-intake/b

echo data > /tank/data/active/pile-intake/a/file.txt
echo data > /tank/data/active/pile-intake/b/file.txt

system-ingest-pile

COUNT=$(grep -c "file.txt$" $PILE/.manifest)
[ "$COUNT" -eq 2 ] || fail "expected two distinct entries"
