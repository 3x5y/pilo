#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/test.txt

echo hello > $FILE

system-manifest-update

(cd "$PILE" && sha256sum --quiet --strict -c .manifest)
