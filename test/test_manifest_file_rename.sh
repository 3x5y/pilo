#!/bin/sh
set -e

PILE=tank/data/active/pile-readonly

echo data > /tmp/file.txt
system-capture /tmp/file.txt
system-ingest-pile

# reorganise
with_dataset_writable $PILE \
    mkdir -p /$PILE/sort
with_dataset_writable $PILE \
    mv /$PILE/in/file.txt /$PILE/sort/file.txt

system-manifest-update

grep -q " \./sort/file.txt$" /$PILE/.manifest \
    || fail "updated path missing"

! grep -q " \./in/file.txt$" /$PILE/.manifest \
    || fail "old path still present"

(cd /$PILE && sha256sum --quiet --strict -c .manifest)
