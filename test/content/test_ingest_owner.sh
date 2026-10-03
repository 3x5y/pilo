#!/bin/sh
set -eu

# simulate capture as root (wrong ownership)
echo data > /"$INTAKE/file.txt"

pilo content-ingest

f=/"$PILE/in/file.txt"
assert_owner $PILO_USER $f
