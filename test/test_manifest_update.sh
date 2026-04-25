#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=$PILE/test2.txt

echo data > $FILE

system-manifest-update

echo more >> $FILE

system-manifest-update

(cd "$PILE" && sha256sum --quiet --strict -c .manifest)

