#!/bin/sh
set -e

file=file.txt

mkintake data $file

pilo content-ingest

assert_file_exists /$PILE/in/$file
assert_not_exists $INTAKE/$file
