#!/bin/sh
set -eu

mkdir "$PILO_INTAKE_PATH"/dir1
echo data > "$PILO_INTAKE_PATH"/dir1/file.txt

pilo content-ingest

d="$PILO_PILE_PATH/in/dir1"
assert_dir_exists "$d"
assert_owner $PILO_USER $d
