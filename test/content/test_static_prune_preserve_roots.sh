#!/bin/sh
set -e

mkdir -p /$PILE/in
mkdir -p /$PILE/out
mkdir -p /$PILE/sort

pilo content-prune

assert_dir_exists /$PILE/in
assert_dir_exists /$PILE/out
assert_dir_exists /$PILE/sort
