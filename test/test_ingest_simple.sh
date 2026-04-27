#!/bin/sh
set -e

INTAKE=/tank/data/active/pile-intake
PILE=/tank/data/active/pile-readonly

echo data > $INTAKE/file.txt

system-ingest-pile

assert_file_exists $PILE/file.txt
assert_not_exists $INTAKE/file.txt
