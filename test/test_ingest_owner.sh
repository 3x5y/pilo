#!/bin/sh
set -eu

# simulate capture as root (wrong ownership)
echo data > "$PILO_INTAKE_PATH/file.txt"

pilo ingest-pile

f="$PILO_PILE_PATH/in/file.txt"
assert_owner $PILO_USER $f
