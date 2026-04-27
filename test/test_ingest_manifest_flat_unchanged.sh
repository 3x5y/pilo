#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

grep -q "./file.txt$" $PILE/.manifest \
    || fail "flat path missing"

(cd $PILE && sha256sum --quiet --strict -c .manifest)
