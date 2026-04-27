#!/bin/sh
set -e

INTAKE=/tank/data/active/pile-intake
PILE=/tank/data/active/pile-readonly

mkdir -p $INTAKE/foo/bar
echo data > $INTAKE/foo/bar/file.txt

system-ingest-pile

assert_file_exists $PILE/in/foo/bar/file.txt
assert_not_exists $PILE/foo/bar/file.txt

