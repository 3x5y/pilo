#!/bin/sh
set -e

INTAKE=/tank/data/active/pile-intake
PILE=/tank/data/active/pile-readonly

mkdir -p $INTAKE/foo
echo data > $INTAKE/foo/file.txt

system-ingest-dir

# re-upload identical
mkdir -p $INTAKE/foo
echo data > $INTAKE/foo/file.txt

system-ingest-dir

assert_file_exists $PILE/in/foo/file.txt
assert_not_exists $INTAKE/foo/file.txt
