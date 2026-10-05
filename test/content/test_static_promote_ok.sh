#!/bin/sh
set -e

file=ok.txt
echo ok > /$PILE/out/collection/$file
create_pile_manifest

pilo content-promote

assert_not_exists /$PILE/out/collection/$file "file still in pile"
assert_file_exists /$STATIC/collection/$file "file not moved to filing"
