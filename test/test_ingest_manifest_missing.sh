#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
FILE=file.txt

echo data > /tmp/$FILE
system-capture /tmp/$FILE

# ensure no manifest exists
rm -f $PILE/.manifest 2>/dev/null || true

system-ingest-pile

assert_file_exists $PILE/.manifest
(cd $PILE && sha256sum --quiet --strict -c .manifest)
