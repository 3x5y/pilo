#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
FILE=test.txt

echo hello > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile
system-manifest-update

(cd "$PILE" && sha256sum --quiet --strict -c .manifest)
