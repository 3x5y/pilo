#!/bin/sh
set -e

FILE=file.txt

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

system-static-promote $FILE collection

# static manifest valid
(cd /tank/data/static/collection && sha256sum --quiet --strict -c .manifest)

# pile manifest valid
system-manifest-verify \
    || fail pile manifest invalid
