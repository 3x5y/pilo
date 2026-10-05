#!/bin/sh
set -e

file=collected.txt
echo data > /$PILE/out/collection/$file
create_pile_manifest

pilo content-promote

assert_file_exists /$STATIC/collection/$file
assert_not_exists /$PILE/out/collection/$file
