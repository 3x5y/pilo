#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
FILE=test.txt

echo data > /tmp/file1.txt
system-capture /tmp/file1.txt
system-ingest-pile
system-manifest-update
echo another > /tmp/file2.txt
system-capture /tmp/file2.txt
system-ingest-pile
system-manifest-update

(cd "$PILE" && sha256sum --quiet --strict -c .manifest)
