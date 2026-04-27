#!/bin/sh
set -e

INTAKE=/tank/data/active/pile-intake
PILE=/tank/data/active/pile-readonly

mkdir -p $INTAKE/a
mkdir -p $INTAKE/b

echo one > $INTAKE/a/1.txt
echo two > $INTAKE/b/2.txt

system-ingest-pile

assert_file_exists $PILE/a/1.txt
assert_file_exists $PILE/b/2.txt
