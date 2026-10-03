#!/bin/sh
set -eu

mkdir /"$INTAKE"/dir1
echo data > /"$INTAKE"/dir1/file.txt

pilo content-ingest

d=/"$PILE/in/dir1"
assert_dir_exists "$d"
assert_owner $PILO_USER $d
