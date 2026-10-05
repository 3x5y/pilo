#!/bin/sh
set -e

mkdir -p /$PILE/out/collection/a
touch /$PILE/out/collection/a/file.txt

pilo content-prune

assert_dir_exists /$PILE/out/collection/a
