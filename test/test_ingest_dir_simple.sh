#!/bin/sh
set -e

INTAKE=/tank/data/active/pile-intake
PILE=/tank/data/active/pile-readonly

mkdir -p $INTAKE/foo
echo data > $INTAKE/foo/file.txt

system-ingest-dir
ls -lR $INTAKE $PILE

assert_file_exists $PILE/in/foo/file.txt
