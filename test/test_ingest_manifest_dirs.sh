#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly

mkdir -p /tank/data/active/pile-intake/foo/bar
echo data > /tank/data/active/pile-intake/foo/bar/file.txt

system-ingest-pile

grep -q "./foo/bar/file.txt$" $PILE/.manifest \
    || fail "missing nested path in manifest"

(cd $PILE && sha256sum --quiet --strict -c .manifest)
