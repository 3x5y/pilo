#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly
FILE=file.txt

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

with_writable $PILE \
    mv /$PILE/in/$FILE /$PILE/out/collection
system-static-promote

# static manifest valid
(cd /tank/data/static && sha256sum --quiet --strict -c .manifest)

# pile manifest valid
system-manifest-verify || fail pile manifest invalid
